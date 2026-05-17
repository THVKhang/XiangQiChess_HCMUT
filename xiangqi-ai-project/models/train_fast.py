"""Fast training script for CPU — uses smaller model architecture.

After training, copies best model to checkpoints/best_model.pth so MLAgent auto-detects it.
"""
import argparse
import os
import sys
import time
import shutil

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from network import XiangQiResNet
from dataset import XiangQiH5Dataset

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def train_fast(data_version: str = "v3", epochs: int = 10):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # Use existing model architecture (5 blocks, 128 channels)
    # but train efficiently with gradient accumulation
    model = XiangQiResNet(num_blocks=5, channels=128).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Model params: {total_params:,}")

    # Load existing weights for fine-tuning
    ckpt = os.path.join(PROJECT, "models", "checkpoints", "best_model.pth")
    if os.path.exists(ckpt):
        sd = torch.load(ckpt, map_location=device, weights_only=True)
        model.load_state_dict(sd, strict=False)
        print(f"Loaded checkpoint for fine-tuning: {ckpt}")
    else:
        print("Training from scratch")

    # Loss & optimizer
    criterion_p = nn.CrossEntropyLoss()
    criterion_v = nn.MSELoss()
    optimizer = optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-2)

    # Data
    train_h5 = os.path.join(PROJECT, "data", f"train_{data_version}.h5")
    val_h5 = os.path.join(PROJECT, "data", f"val_{data_version}.h5")

    if not os.path.exists(train_h5):
        print(f"ERROR: {train_h5} not found. Run preprocess.py first.")
        return

    train_ds = XiangQiH5Dataset(train_h5)
    val_ds = XiangQiH5Dataset(val_h5)
    
    # Smaller batch size for CPU stability
    train_loader = DataLoader(train_ds, batch_size=128, shuffle=False, pin_memory=False, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=128, shuffle=False, pin_memory=False, num_workers=0)
    print(f"Train: {len(train_ds)} samples ({len(train_loader)} batches)")
    print(f"Val: {len(val_ds)} samples ({len(val_loader)} batches)")

    num_epochs = epochs
    scheduler = CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=1e-5)

    save_dir = os.path.join(PROJECT, "models", "checkpoints")
    os.makedirs(save_dir, exist_ok=True)
    best_path = os.path.join(save_dir, "best_model.pth")
    best_val_loss = float("inf")

    print(f"\n{'='*60}")
    print(f"TRAINING {num_epochs} epochs")
    print(f"{'='*60}")

    t0 = time.time()
    for epoch in range(num_epochs):
        ep_start = time.time()

        # ── Train ──
        model.train()
        train_loss, correct, total = 0.0, 0, 0
        for batch_idx, (x, (yp, yv)) in enumerate(train_loader):
            x = x.to(device)
            yp = yp.to(device)
            yv = yv.to(device)

            optimizer.zero_grad()
            pp, pv = model(x)
            loss = criterion_p(pp, yp) + criterion_v(pv, yv)
            loss.backward()
            optimizer.step()

            train_loss += loss.item()
            correct += (pp.argmax(1) == yp).sum().item()
            total += x.size(0)

            # Progress dots
            if (batch_idx + 1) % 10 == 0:
                print(".", end="", flush=True)

        avg_train = train_loss / max(1, len(train_loader))
        train_acc = correct / max(1, total) * 100

        # ── Validate ──
        model.eval()
        val_loss_sum, v_correct, v_total = 0.0, 0, 0
        with torch.no_grad():
            for x, (yp, yv) in val_loader:
                x = x.to(device)
                yp = yp.to(device)
                yv = yv.to(device)
                pp, pv = model(x)
                val_loss_sum += (criterion_p(pp, yp) + criterion_v(pv, yv)).item()
                v_correct += (pp.argmax(1) == yp).sum().item()
                v_total += x.size(0)

        avg_val = val_loss_sum / max(1, len(val_loader))
        val_acc = v_correct / max(1, v_total) * 100
        scheduler.step()

        mark = ""
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            torch.save(model.state_dict(), best_path)
            mark = " *BEST*"

        elapsed = time.time() - ep_start
        total_elapsed = time.time() - t0
        lr_now = optimizer.param_groups[0]["lr"]
        print(
            f"\nE{epoch+1:02d}/{num_epochs} "
            f"TL={avg_train:.4f} TA={train_acc:.1f}% "
            f"VL={avg_val:.4f} VA={val_acc:.1f}% "
            f"LR={lr_now:.5f} "
            f"({elapsed:.0f}s, total {total_elapsed:.0f}s){mark}"
        )

    print(f"\n{'='*60}")
    print(f"DONE! Best val loss: {best_val_loss:.4f}")
    print(f"Model saved to: {best_path}")
    print(f"Total time: {time.time()-t0:.0f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="v3", help="Data version: v2 (sample) or v3 (full)")
    parser.add_argument("--epochs", type=int, default=10)
    args = parser.parse_args()
    train_fast(data_version=args.data, epochs=args.epochs)
