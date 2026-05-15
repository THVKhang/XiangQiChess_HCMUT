import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.cuda.amp import autocast, GradScaler
from dataset import get_dataloader
from network import XiangQiResNet
from torch.utils.tensorboard import SummaryWriter

def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except Exception:
        return default

def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default

def calculate_value_accuracy(outputs, targets, threshold=0.33):
    """
    Tính Accuracy cho Value Head bằng cách làm tròn Output:
    > threshold  -> 1.0 (Thắng)
    < -threshold -> -1.0 (Thua)
    Còn lại     -> 0.0 (Hòa)
    """
    preds = torch.zeros_like(outputs)
    preds[outputs > threshold] = 1.0
    preds[outputs < -threshold] = -1.0
    correct = (preds == targets).sum()
    return correct / targets.size(0)

def calculate_policy_accuracy(outputs, targets):
    """Tính Top-1 Accuracy cho Policy Head."""
    preds = torch.argmax(outputs, dim=1)
    correct = (preds == targets).sum()
    return correct / targets.size(0)

def train():
    # 1. Cấu hình thiết bị
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    run_name = os.getenv("XIANGQI_RUN_NAME", "xiangqi_experiment_1")
    reset = _env_flag("XIANGQI_RESET", False)
    num_epochs = _env_int("XIANGQI_EPOCHS", 50)
    batch_size = _env_int("XIANGQI_BATCH_SIZE", 1024)
    num_workers = _env_int("XIANGQI_NUM_WORKERS", 2)
    train_batch_limit = _env_int("XIANGQI_TRAIN_BATCH_LIMIT", 0)
    val_batch_limit = _env_int("XIANGQI_VAL_BATCH_LIMIT", 0)
    lr = _env_float("XIANGQI_LR", 1e-3)
    weight_decay = _env_float("XIANGQI_WEIGHT_DECAY", 1e-2)

    # 2. Khởi tạo mô hình
    model = XiangQiResNet(num_blocks=5, channels=128).to(device)
    
    # 3. Setup Loss Function, Optimizer, và Learning Rate Scheduler
    criterion_v = nn.MSELoss()
    criterion_p = nn.CrossEntropyLoss()
    
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=2)
    
    # 4. Cấu hình thư mục và Dataloader
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    save_dir = os.getenv("XIANGQI_SAVE_DIR") or os.path.join(current_dir, "checkpoints")
    os.makedirs(save_dir, exist_ok=True)
    
    project_dir = os.path.dirname(current_dir)
    train_h5_path = os.path.join(project_dir, "data", "xiangqi_train.h5") # Đổi tên vì preprocess tạo thẳng file này
    val_h5_path = os.path.join(project_dir, "data", "xiangqi_val.h5")
    
    print(f"Preparing Train and Val DataLoaders from HDF5...")
    train_loader = get_dataloader(train_h5_path, batch_size=batch_size, num_workers=num_workers)
    val_loader = get_dataloader(val_h5_path, batch_size=batch_size, num_workers=num_workers)
    
    # 5. Thông số vòng lặp và Resume Training Logic
    start_epoch = 0
    best_val_loss = float('inf')
    patience = 5  
    early_stop_counter = 0
    
    # Load model từ best_model.pth (Fine-tuning / Transfer Learning)
    best_model_path = os.path.join(save_dir, "best_model.pth")
    if (not reset) and os.path.exists(best_model_path):
        print(f"\n[INFO] Tìm thấy file best_model: {best_model_path}")
        print("[INFO] Bắt đầu quá trình Fine-tuning từ trọng số này.")
        state_dict = torch.load(best_model_path, map_location=device)
        # strict=False cho phép load các trọng số cũ vào backbone, bỏ qua Policy Head mới
        model.load_state_dict(state_dict, strict=False)
        start_epoch = 0
        best_val_loss = float('inf')
    else:
        print("\n[INFO] Học từ đầu (reset hoặc không có best_model cũ).")
        
    log_dir = os.path.join(current_dir, "runs", run_name)
    writer = SummaryWriter(log_dir=log_dir)
    print(f"TensorBoard logging at: {log_dir}")
    
    scaler = GradScaler()

    print("\nSTARTING TRAINING PROCESS...")
    
    for epoch in range(start_epoch, num_epochs):
        
        # --- TRAINING PHASE ---
        model.train()
        train_loss = torch.tensor(0.0, device=device)
        train_loss_p = torch.tensor(0.0, device=device)
        train_loss_v = torch.tensor(0.0, device=device)
        train_acc_p = torch.tensor(0.0, device=device)
        train_acc_v = torch.tensor(0.0, device=device)
        train_batches = 0
        
        print(f"\n--- Epoch {epoch+1}/{num_epochs} [LR: {scheduler.get_last_lr()[0]:.1e}] ---")
        
        for batch_idx, (inputs, (targets_p, targets_v)) in enumerate(train_loader):
            if train_batch_limit > 0 and batch_idx >= train_batch_limit:
                break
            inputs, targets_p, targets_v = inputs.to(device), targets_p.to(device), targets_v.to(device)
            
            optimizer.zero_grad()
            
            with autocast():
                outputs_p, outputs_v = model(inputs)
                loss_p = criterion_p(outputs_p, targets_p)
                loss_v = criterion_v(outputs_v, targets_v)
                loss = loss_p + loss_v # Combined Loss
                
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            acc_p = calculate_policy_accuracy(outputs_p, targets_p)
            acc_v = calculate_value_accuracy(outputs_v, targets_v)
            
            train_loss += loss
            train_loss_p += loss_p
            train_loss_v += loss_v
            train_acc_p += acc_p
            train_acc_v += acc_v
            train_batches += 1
            
            global_step = epoch * len(train_loader) + batch_idx
            writer.add_scalar('Loss/Train_Total_Step', loss.item(), global_step)
            writer.add_scalar('Loss/Train_Policy_Step', loss_p.item(), global_step)
            writer.add_scalar('Loss/Train_Value_Step', loss_v.item(), global_step)
            writer.add_scalar('Accuracy/Train_Policy_Step', acc_p.item(), global_step)
            writer.add_scalar('Accuracy/Train_Value_Step', acc_v.item(), global_step)
            
            if (batch_idx + 1) % 10 == 0:
                avg_loss = train_loss.item() / train_batches
                avg_acc_p = train_acc_p.item() / train_batches
                avg_acc_v = train_acc_v.item() / train_batches
                print(f"Train | Batch {batch_idx+1} | Loss: {avg_loss:.4f} | Acc P: {avg_acc_p:.2%} | Acc V: {avg_acc_v:.2%}")
                
        # --- VALIDATION PHASE ---
        model.eval()
        val_loss = torch.tensor(0.0, device=device)
        val_loss_p = torch.tensor(0.0, device=device)
        val_loss_v = torch.tensor(0.0, device=device)
        val_acc_p = torch.tensor(0.0, device=device)
        val_acc_v = torch.tensor(0.0, device=device)
        val_batches = 0
        
        print(f"Running Validation...")
        with torch.no_grad():
            for batch_idx, (inputs, (targets_p, targets_v)) in enumerate(val_loader):
                if val_batch_limit > 0 and batch_idx >= val_batch_limit:
                    break
                inputs, targets_p, targets_v = inputs.to(device), targets_p.to(device), targets_v.to(device)
                
                with autocast():
                    outputs_p, outputs_v = model(inputs)
                    loss_p = criterion_p(outputs_p, targets_p)
                    loss_v = criterion_v(outputs_v, targets_v)
                    loss = loss_p + loss_v
                    
                acc_p = calculate_policy_accuracy(outputs_p, targets_p)
                acc_v = calculate_value_accuracy(outputs_v, targets_v)
                
                val_loss += loss
                val_loss_p += loss_p
                val_loss_v += loss_v
                val_acc_p += acc_p
                val_acc_v += acc_v
                val_batches += 1
        
        avg_train_loss = train_loss.item() / max(1, train_batches)
        avg_train_loss_p = train_loss_p.item() / max(1, train_batches)
        avg_train_loss_v = train_loss_v.item() / max(1, train_batches)
        avg_train_acc_p = train_acc_p.item() / max(1, train_batches)
        avg_train_acc_v = train_acc_v.item() / max(1, train_batches)
        
        avg_val_loss = val_loss.item() / max(1, val_batches)
        avg_val_loss_p = val_loss_p.item() / max(1, val_batches)
        avg_val_loss_v = val_loss_v.item() / max(1, val_batches)
        avg_val_acc_p = val_acc_p.item() / max(1, val_batches)
        avg_val_acc_v = val_acc_v.item() / max(1, val_batches)
        
        # Cập nhật Learning Rate Scheduler dựa trên Total Validation Loss
        scheduler.step(avg_val_loss)
        
        writer.add_scalar('Loss/Train_Total_Epoch', avg_train_loss, epoch)
        writer.add_scalar('Loss/Train_Policy_Epoch', avg_train_loss_p, epoch)
        writer.add_scalar('Loss/Train_Value_Epoch', avg_train_loss_v, epoch)
        writer.add_scalar('Accuracy/Train_Policy_Epoch', avg_train_acc_p, epoch)
        writer.add_scalar('Accuracy/Train_Value_Epoch', avg_train_acc_v, epoch)
        
        writer.add_scalar('Loss/Validation_Total_Epoch', avg_val_loss, epoch)
        writer.add_scalar('Loss/Validation_Policy_Epoch', avg_val_loss_p, epoch)
        writer.add_scalar('Loss/Validation_Value_Epoch', avg_val_loss_v, epoch)
        writer.add_scalar('Accuracy/Validation_Policy_Epoch', avg_val_acc_p, epoch)
        writer.add_scalar('Accuracy/Validation_Value_Epoch', avg_val_acc_v, epoch)
        
        current_lr = optimizer.param_groups[0]['lr']
        writer.add_scalar('Learning_Rate', current_lr, epoch)
        
        print(f"Epoch {epoch+1} Summary:")
        print(f"Train - Loss: {avg_train_loss:.4f} (P: {avg_train_loss_p:.4f}, V: {avg_train_loss_v:.4f}) | Acc P: {avg_train_acc_p:.2%} | Acc V: {avg_train_acc_v:.2%}")
        print(f"Val   - Loss: {avg_val_loss:.4f} (P: {avg_val_loss_p:.4f}, V: {avg_val_loss_v:.4f}) | Acc P: {avg_val_acc_p:.2%} | Acc V: {avg_val_acc_v:.2%}")
                
        # --- LƯU CHECKPOINT ---
        if train_batches > 0:
            if avg_val_loss < best_val_loss:
                best_val_loss = avg_val_loss
                early_stop_counter = 0 
                
                best_model_path = os.path.join(save_dir, "best_model.pth")
                torch.save(model.state_dict(), best_model_path)
                print(f"🔥 NEW BEST MODEL SAVED: {best_model_path} (Val Loss: {best_val_loss:.4f})")
            else:
                early_stop_counter += 1
                print(f"⚠️ Không cải thiện. Early Stopping Counter: {early_stop_counter}/{patience}")
                
                if early_stop_counter >= patience:
                    print(f"\n🛑 EARLY STOPPING ĐÃ ĐƯỢC KÍCH HOẠT! Dừng huấn luyện sớm để tránh Overfitting.")
                    break
        else:
            print("Warning: No data passed through the network in this epoch.")
            
    writer.close()

if __name__ == "__main__":
    train()
