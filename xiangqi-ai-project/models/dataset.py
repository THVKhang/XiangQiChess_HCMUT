import h5py
import torch
import os
from torch.utils.data import Dataset, DataLoader

class XiangQiH5Dataset(Dataset):
    def __init__(self, h5_path, chunk_size=100000):
        """
        Dataloader dạng Offline sử dụng HDF5. 
        Đã tối ưu hóa đọc theo chunk để tránh thắt cổ chai I/O khi shuffle.
        """
        self.h5_path = h5_path
        self.chunk_size = chunk_size
        self.h5_file = None
        
        # Biến đệm Chunk
        self.current_chunk_idx = -1
        self.states_chunk = None
        self.policies_chunk = None
        self.targets_chunk = None
        
        if not os.path.exists(self.h5_path):
            raise FileNotFoundError(f"Không tìm thấy file HDF5: {self.h5_path}. Vui lòng chạy preprocess.py trước!")
            
        # Mở file một lần để đếm số lượng data
        with h5py.File(self.h5_path, 'r') as f:
            self.length = f['targets'].shape[0]

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        # Tránh lỗi multi-processing của PyTorch khi đọc file HDF5
        if self.h5_file is None:
            self.h5_file = h5py.File(self.h5_path, 'r')
            
        # Xác định index của chunk chứa dữ liệu này
        chunk_idx = idx // self.chunk_size
        
        # Nếu chunk chưa có trên RAM, đọc nguyên chunk từ ổ cứng (Rất nhanh)
        if chunk_idx != self.current_chunk_idx:
            start = chunk_idx * self.chunk_size
            end = min(start + self.chunk_size, self.length)
            self.states_chunk = self.h5_file['states'][start:end]
            self.policies_chunk = self.h5_file['policies'][start:end]
            self.targets_chunk = self.h5_file['targets'][start:end]
            self.current_chunk_idx = chunk_idx
            
        # Lấy dữ liệu từ chunk đã cache trên RAM
        local_idx = idx % self.chunk_size
        state_int8 = self.states_chunk[local_idx]
        policy_target = self.policies_chunk[local_idx]
        value_target = self.targets_chunk[local_idx]
        
        # Chuyển int8 thành float32 để nhét vào mô hình ResNet
        x = torch.from_numpy(state_int8).float()
        y_policy = torch.tensor(policy_target, dtype=torch.long)
        y_value = torch.tensor(value_target, dtype=torch.float32)
        
        return x, (y_policy, y_value)

from torch.utils.data import Sampler
import random

class ChunkedRandomSampler(Sampler):
    """
    Sampler đặc biệt để dùng chung với HDF5 Chunking.
    Nó sẽ trả về các index ngẫu nhiên, nhưng luôn gom theo từng Chunk.
    Nhờ đó DataLoader sẽ không nhảy cóc liên tục khắp file HDF5.
    """
    def __init__(self, data_source, chunk_size):
        self.data_source = data_source
        self.chunk_size = chunk_size
        
    def __iter__(self):
        n = len(self.data_source)
        chunk_starts = list(range(0, n, self.chunk_size))
        # Trộn ngẫu nhiên thứ tự đọc các chunk
        random.shuffle(chunk_starts)
        
        for start in chunk_starts:
            end = min(start + self.chunk_size, n)
            chunk_indices = list(range(start, end))
            # Trộn ngẫu nhiên các phần tử bên trong chunk
            random.shuffle(chunk_indices)
            for idx in chunk_indices:
                yield idx
                
    def __len__(self):
        return len(self.data_source)

def get_dataloader(h5_path, batch_size=64, num_workers=0):
    chunk_size = 100000
    dataset = XiangQiH5Dataset(h5_path, chunk_size=chunk_size)
    
    # Sử dụng ChunkedRandomSampler thay cho shuffle=True
    sampler = ChunkedRandomSampler(dataset, chunk_size=chunk_size)
    
    # pin_memory=True giúp chuyển dữ liệu từ RAM lên GPU nhanh hơn.
    return DataLoader(dataset, batch_size=batch_size, sampler=sampler, num_workers=num_workers, pin_memory=True)

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_h5 = os.path.join(current_dir, "../data/xiangqi_val.h5")
    
    if os.path.exists(test_h5):
        loader = get_dataloader(test_h5, batch_size=4)
        print("Starting Offline HDF5 dataloader test...")
        for batch_idx, (x, (y_p, y_v)) in enumerate(loader):
            print(f"--- Batch {batch_idx+1} ---")
            print(f"Batch X shape: {x.shape} -> (Batch_size, Channels, Rows, Cols)")
            print(f"Batch Y_Policy shape: {y_p.shape} -> (Batch_size,)")
            print(f"Batch Y_Value shape: {y_v.shape} -> (Batch_size, 1)")
            print(f"Y_Policy values: {y_p.tolist()}")
            print(f"Y_Value values: {y_v.view(-1).tolist()}")
            if batch_idx >= 2:
                break
    else:
        print(f"Không tìm thấy file test: {test_h5}. Chạy file preprocess.py trước.")
