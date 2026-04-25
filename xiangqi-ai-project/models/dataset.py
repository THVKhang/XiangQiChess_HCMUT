import json
import os
import sys
import torch
from torch.utils.data import IterableDataset, DataLoader, get_worker_info

# Setup sys.path để truy cập được core và tools
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.rules import Color
from core.move_generator import legal_moves
from core.encoding import state_to_tensor
from tools.validate_pgn_legality import from_fen, move_notations, normalize_token


class XiangQiIterableDataset(IterableDataset):
    def __init__(self, jsonl_path, canonical=False):
        """
        Dataloader dạng Online. Đọc file JSONL, giả lập từng ván cờ và tạo ra Tensor cho mỗi nước đi.
        - canonical (bool): Nếu True, luôn xoay bàn cờ về hướng của người đang đến lượt (như AlphaZero).
        """
        self.jsonl_path = jsonl_path
        self.canonical = canonical

    def __iter__(self):
        worker_info = get_worker_info()
        worker_id = worker_info.id if worker_info is not None else 0
        num_workers = worker_info.num_workers if worker_info is not None else 1
        
        if not os.path.exists(self.jsonl_path):
            print(f"Cảnh báo: Không tìm thấy file {self.jsonl_path}")
            return

        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line_idx, line in enumerate(f):
                # Phân chia dữ liệu cho các worker để tăng tốc bằng Multi-processing
                if line_idx % num_workers != worker_id:
                    continue
                    
                if not line.strip():
                    continue
                    
                try:
                    obj = json.loads(line)
                    fen = obj.get('fen', '')
                    result = obj.get('headers', {}).get('Result', '')
                    moves = obj.get('moves', [])
                    
                    if not fen or result not in ['1-0', '0-1', '1/2-1/2']:
                        continue
                        
                    yield from self.process_game(fen, moves, result)
                except Exception:
                    continue

    def process_game(self, fen, moves, result):
        # 1.0: Đỏ thắng | 0.0: Đen thắng | 0.5: Hòa
        if result == '1-0': base_val = 1.0
        elif result == '0-1': base_val = 0.0
        else: base_val = 0.5
        
        try:
            state = from_fen(fen)
        except Exception:
            return
            
        # Hàm tính target value tùy theo cấu hình canonical
        def get_target(current_state):
            if not self.canonical:
                return base_val # Luôn dự đoán % Đỏ thắng
            else:
                # Nếu xoay bàn cờ theo người đang đi, dự đoán tỉ lệ thắng của NGƯỜI ĐÓ
                return base_val if current_state.side_to_move == Color.RED else (1.0 - base_val)

        try:
            # Yield trạng thái đầu tiên của ván
            t_state = state_to_tensor(state, channels_first=True, canonical=self.canonical, as_numpy=True)
            yield torch.from_numpy(t_state).float(), torch.tensor([get_target(state)], dtype=torch.float32)

            # Giả lập từng nước đi để lấy trạng thái trung gian
            for raw_move in moves:
                token = normalize_token(raw_move)
                if not token:
                    continue
                    
                candidates = legal_moves(state)
                matched = None
                
                # Check nước đi theo chuẩn
                for mv in candidates:
                    if token in move_notations(state, mv, include_absolute=False):
                        matched = mv
                        break
                        
                # Fallback: check theo toạ độ tuyệt đối
                if not matched:
                    for mv in candidates:
                        if token in move_notations(state, mv, include_absolute=True):
                            matched = mv
                            break
                
                if not matched:
                    break # Nếu nước đi không hợp lệ hoặc không parse được, bỏ qua phần còn lại của ván
                    
                state.apply_move(matched)
                
                t_state = state_to_tensor(state, channels_first=True, canonical=self.canonical, as_numpy=True)
                yield torch.from_numpy(t_state).float(), torch.tensor([get_target(state)], dtype=torch.float32)
        except Exception:
            pass


def get_dataloader(jsonl_path, batch_size=32, num_workers=0, canonical=False):
    """
    Tạo DataLoader cho Online Iterable Dataset.
    Chú ý: IterableDataset không hỗ trợ shuffle=True. Dữ liệu sẽ được đọc theo trình tự file.
    """
    dataset = XiangQiIterableDataset(jsonl_path, canonical=canonical)
    return DataLoader(dataset, batch_size=batch_size, num_workers=num_workers)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "../data/ccpd_parsed.jsonl")
    
    # Run test loader
    loader = get_dataloader(dataset_path, batch_size=4, num_workers=0)
    
    print("Starting online dataloader test...")
    for batch_idx, (x, y) in enumerate(loader):
        print(f"--- Batch {batch_idx+1} ---")
        print(f"Batch X shape: {x.shape} -> (Batch_size, Channels, Rows, Cols)")
        print(f"Batch Y shape: {y.shape} -> (Batch_size, 1)")
        print(f"Y values: {y.view(-1).tolist()}")
        if batch_idx >= 2: # Stop after 3 batches
            break
