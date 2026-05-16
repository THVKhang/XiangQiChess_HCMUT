import h5py
import numpy as np
import os
import gc

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, desc="", **kwargs):
        print(f"{desc}...")
        return iterable

def append_to_dataset(ds, data):
    if len(data) == 0:
        return
    current_size = ds.shape[0]
    new_size = current_size + len(data)
    ds.resize(new_size, axis=0)
    ds[current_size:new_size] = data

def scatter_to_buckets(input_h5, temp_h5, num_buckets=10, chunk_size=100000):
    print(f"\n--- PASS 1: Phân mảnh (Scatter) vào {num_buckets} buckets tạm thời ---")
    with h5py.File(input_h5, 'r') as f_in, h5py.File(temp_h5, 'w') as f_temp:
        states_in = f_in['states']
        targets_in = f_in['targets']
        total_items = states_in.shape[0]
        
        print(f"Tổng số dữ liệu cần xử lý: {total_items}")
        
        # Khởi tạo các dataset bucket
        buckets_s = []
        buckets_t = []
        for i in range(num_buckets):
            bs = f_temp.create_dataset(f'bucket_{i}_states', shape=(0, 15, 10, 9), maxshape=(None, 15, 10, 9), dtype='int8', chunks=True)
            bt = f_temp.create_dataset(f'bucket_{i}_targets', shape=(0, 1), maxshape=(None, 1), dtype='float32', chunks=True)
            buckets_s.append(bs)
            buckets_t.append(bt)
            
        num_chunks = (total_items + chunk_size - 1) // chunk_size
        
        for i in tqdm(range(num_chunks), desc="Đang phân mảnh (Scatter)"):
            start = i * chunk_size
            end = min(start + chunk_size, total_items)
            
            chunk_s = states_in[start:end]
            chunk_t = targets_in[start:end]
            
            # Gán ngẫu nhiên mỗi điểm dữ liệu vào 1 trong 10 buckets
            bucket_assignments = np.random.randint(0, num_buckets, size=(end - start,))
            
            for b in range(num_buckets):
                mask = (bucket_assignments == b)
                if np.any(mask):
                    append_to_dataset(buckets_s[b], chunk_s[mask])
                    append_to_dataset(buckets_t[b], chunk_t[mask])

def gather_and_shuffle(temp_h5, output_h5, num_buckets=10):
    print(f"\n--- PASS 2: Xáo trộn trong RAM và Gom (Gather) ---")
    with h5py.File(temp_h5, 'r') as f_temp, h5py.File(output_h5, 'w') as f_out:
        out_s = f_out.create_dataset('states', shape=(0, 15, 10, 9), maxshape=(None, 15, 10, 9), dtype='int8', chunks=True)
        out_t = f_out.create_dataset('targets', shape=(0, 1), maxshape=(None, 1), dtype='float32', chunks=True)
        
        for i in tqdm(range(num_buckets), desc="Đang xáo trộn (Shuffle & Gather)"):
            # Đọc trọn vẹn 1 bucket lên RAM (~1.2GB)
            bs = f_temp[f'bucket_{i}_states'][:]
            bt = f_temp[f'bucket_{i}_targets'][:]
            
            if len(bs) > 0:
                # Xáo trộn hoàn hảo trong RAM
                idx = np.random.permutation(len(bs))
                shuffled_s = bs[idx]
                shuffled_t = bt[idx]
                
                # Ghi vào file kết quả cuối cùng
                append_to_dataset(out_s, shuffled_s)
                append_to_dataset(out_t, shuffled_t)
                
            # Giải phóng RAM cho vòng lặp tiếp theo
            del bs, bt, shuffled_s, shuffled_t, idx
            gc.collect()

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), "data")
    
    input_file = os.path.join(data_dir, "xiangqi_train.h5")
    temp_file = os.path.join(data_dir, "xiangqi_temp.h5")
    output_file = os.path.join(data_dir, "xiangqi_train_shuffled.h5")
    
    if not os.path.exists(input_file):
        print(f"Lỗi: Không tìm thấy file {input_file}. Bạn hãy kiểm tra lại!")
        exit(1)
        
    print("===================================================")
    print(" BẮT ĐẦU GLOBAL SHUFFLE (OUT-OF-CORE BUCKET SHUFFLE) ")
    print("===================================================")
    
    try:
        scatter_to_buckets(input_file, temp_file, num_buckets=10, chunk_size=200000)
        gather_and_shuffle(temp_file, output_file, num_buckets=10)
        
        print(f"\n✅ Hoàn tất! Đã tạo file xáo trộn tại: {output_file}")
        print(f"Đang dọn dẹp file tạm...")
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        print("🎉 Bạn có thể chạy train.py ngay bây giờ!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Đã hủy bởi người dùng.")
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception as e:
        print(f"\n❌ Có lỗi xảy ra: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
