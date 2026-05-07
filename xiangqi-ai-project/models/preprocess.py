import h5py
import numpy as np
import json
import os
import sys

# Setup sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.rules import Color
from core.move_generator import legal_moves
from core.encoding import state_to_tensor
from tools.validate_pgn_legality import from_fen, move_notations, normalize_token
from core.policy_encoding import canonical_move_to_policy_index, move_to_policy_index

def flip_policy_index(idx):
    src_idx = idx // 90
    dst_idx = idx % 90
    src_r, src_c = src_idx // 9, src_idx % 9
    dst_r, dst_c = dst_idx // 9, dst_idx % 9
    f_src_c, f_dst_c = 8 - src_c, 8 - dst_c
    f_src_idx = src_r * 9 + f_src_c
    f_dst_idx = dst_r * 9 + f_dst_c
    return f_src_idx * 90 + f_dst_idx

def process_game(fen, move_labels, result, canonical=False):
    # 1.0: Win | -1.0: Loss | 0.0: Draw
    if result == '1-0': base_val = 1.0
    elif result == '0-1': base_val = -1.0
    else: base_val = 0.0
    
    try:
        state = from_fen(fen)
    except Exception:
        return []
        
    def get_target(current_state):
        if not canonical:
            return base_val
        else:
            return base_val if current_state.side_to_move == Color.RED else -base_val

    data = []
    try:
        for m_dict in move_labels:
            if not m_dict.get('is_legal'): break
            raw_move = m_dict['move']
            
            token = normalize_token(raw_move)
            if not token: continue
                
            candidates = legal_moves(state)
            matched = None
            
            for mv in candidates:
                if token in move_notations(state, mv, include_absolute=False):
                    matched = mv
                    break
                    
            if not matched:
                for mv in candidates:
                    if token in move_notations(state, mv, include_absolute=True):
                        matched = mv
                        break
            
            if not matched: break
            
            # Extract Policy Target before applying the move
            if canonical:
                policy_idx = canonical_move_to_policy_index(matched, state.side_to_move)
            else:
                policy_idx = move_to_policy_index(matched)
                
            t_state = state_to_tensor(state, channels_first=True, canonical=canonical, as_numpy=True)
            data.append((t_state, policy_idx, get_target(state)))
            
            state.apply_move(matched)
            
    except Exception:
        pass
    
    return data

def append_to_h5(states_ds, policies_ds, targets_ds, buffer_states, buffer_policies, buffer_targets):
    if len(buffer_states) == 0:
        return 0
    current_size = states_ds.shape[0]
    new_size = current_size + len(buffer_states)
    states_ds.resize(new_size, axis=0)
    policies_ds.resize(new_size, axis=0)
    targets_ds.resize(new_size, axis=0)
    
    states_ds[current_size:new_size] = np.array(buffer_states, dtype=np.int8)
    policies_ds[current_size:new_size] = np.array(buffer_policies, dtype=np.int16)
    targets_ds[current_size:new_size] = np.array(buffer_targets, dtype=np.float32)
    return len(buffer_states)

def build_hdf5_dataset(jsonl_path, train_h5_path, val_h5_path, split_ratio=0.8, canonical=True):
    print("Starting Data Quantization (JSONL to HDF5 int8)...")
    
    with h5py.File(train_h5_path, 'w') as train_h5, h5py.File(val_h5_path, 'w') as val_h5:
        # Create datasets
        t_states = train_h5.create_dataset('states', shape=(0, 15, 10, 9), maxshape=(None, 15, 10, 9), dtype='int8', chunks=True)
        t_policies = train_h5.create_dataset('policies', shape=(0,), maxshape=(None,), dtype='int16', chunks=True)
        t_targets = train_h5.create_dataset('targets', shape=(0, 1), maxshape=(None, 1), dtype='float32', chunks=True)
        
        v_states = val_h5.create_dataset('states', shape=(0, 15, 10, 9), maxshape=(None, 15, 10, 9), dtype='int8', chunks=True)
        v_policies = val_h5.create_dataset('policies', shape=(0,), maxshape=(None,), dtype='int16', chunks=True)
        v_targets = val_h5.create_dataset('targets', shape=(0, 1), maxshape=(None, 1), dtype='float32', chunks=True)
        
        t_buf_s, t_buf_p, t_buf_t = [], [], []
        v_buf_s, v_buf_p, v_buf_t = [], [], []
        
        total_train = 0
        total_val = 0
        
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                if not line.strip(): continue
                
                try:
                    obj = json.loads(line)
                    fen = obj.get('fen', '')
                    result = obj.get('headers', {}).get('Result', '')
                    
                    # Ensure the game has all_moves_legal true to avoid bad data
                    if not obj.get('all_moves_legal', False):
                        continue
                        
                    move_labels = obj.get('move_labels', [])
                    
                    if not fen or result not in ['1-0', '0-1', '1/2-1/2'] or not move_labels:
                        continue
                        
                    game_data = process_game(fen, move_labels, result, canonical)
                    if not game_data:
                        continue
                        
                    is_train = (line_idx % 10) < int(split_ratio * 10)
                    
                    for state_arr, policy_idx, target_val in game_data:
                        # INT8 Quantization
                        state_int8 = state_arr.astype(np.int8)
                        
                        # Data Augmentation: Lật gương ngang bàn cờ (Horizontal Flip)
                        state_int8_flipped = np.flip(state_int8, axis=2).copy()
                        policy_idx_flipped = flip_policy_index(policy_idx)
                        
                        if is_train:
                            t_buf_s.append(state_int8)
                            t_buf_p.append(policy_idx)
                            t_buf_t.append([target_val])
                            # Thêm bản lật gương vào train
                            t_buf_s.append(state_int8_flipped)
                            t_buf_p.append(policy_idx_flipped)
                            t_buf_t.append([target_val])
                        else:
                            v_buf_s.append(state_int8)
                            v_buf_p.append(policy_idx)
                            v_buf_t.append([target_val])
                            # Thêm bản lật gương vào val
                            v_buf_s.append(state_int8_flipped)
                            v_buf_p.append(policy_idx_flipped)
                            v_buf_t.append([target_val])
                            
                    # Flush buffers
                    if len(t_buf_s) >= 5000:
                        total_train += append_to_h5(t_states, t_policies, t_targets, t_buf_s, t_buf_p, t_buf_t)
                        print(f"Saved {total_train} train states to HDF5...")
                        t_buf_s, t_buf_p, t_buf_t = [], [], []
                        
                    if len(v_buf_s) >= 5000:
                        total_val += append_to_h5(v_states, v_policies, v_targets, v_buf_s, v_buf_p, v_buf_t)
                        print(f"Saved {total_val} val states to HDF5...")
                        v_buf_s, v_buf_p, v_buf_t = [], [], []
                        
                except Exception:
                    continue
                    
        # Flush remaining
        total_train += append_to_h5(t_states, t_policies, t_targets, t_buf_s, t_buf_p, t_buf_t)
        total_val += append_to_h5(v_states, v_policies, v_targets, v_buf_s, v_buf_p, v_buf_t)
        
    print(f"Finished! Saved {total_train} Train states and {total_val} Val states.")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    jsonl_path = os.path.join(current_dir, "../data/ccpd_labeled.jsonl")
    train_h5 = os.path.join(current_dir, "../data/xiangqi_train.h5")
    val_h5 = os.path.join(current_dir, "../data/xiangqi_val.h5")
    
    build_hdf5_dataset(jsonl_path, train_h5, val_h5, canonical=True)
