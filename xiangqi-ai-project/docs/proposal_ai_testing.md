# Đề xuất test AI (tự đi) và AI học từ data

## Mục tiêu
- Chứng minh AI “biết đi” (tạo nước hợp lệ, chạy ổn định, không crash).
- Chứng minh “học từ data” có tác động (so sánh trước/sau train qua chỉ số định lượng).
- Có quy trình test lặp lại được (reproducible) và dễ demo.

## Định nghĩa 2 case cần test
- **Case A — AI tự đi (không học / baseline):** dùng `MLAgent` với `model_path=None` (DummyPolicyModel) hoặc dùng SearchAgent/RandomAgent làm baseline.
- **Case B — AI học từ data:** train bằng `models/train.py` để tạo `models/checkpoints/best_model.pth`, sau đó chạy `MLAgent(model_path=best_model.pth)`.

## Pipeline dữ liệu & train (tạo “AI học từ data”)
### 1) Tạo dataset HDF5 từ sample JSONL
```bash
cd /Users/nguyenducgiabao/XiangQiChess_HCMUT/xiangqi-ai-project
.venv/bin/python - <<'PY'
from pathlib import Path
from models.preprocess import build_hdf5_dataset

p = Path('.').resolve()
build_hdf5_dataset(
  jsonl_path=str(p/'data/ccpd_labeled_sample.jsonl'),
  train_h5_path=str(p/'data/xiangqi_train.h5'),
  val_h5_path=str(p/'data/xiangqi_val.h5'),
  split_ratio=0.8,
  canonical=True
)
PY
```

### 2) Train nhanh để demo (có log + TensorBoard)
```bash
cd /Users/nguyenducgiabao/XiangQiChess_HCMUT/xiangqi-ai-project/models
XIANGQI_RUN_NAME=demo_train \
XIANGQI_RESET=1 \
XIANGQI_EPOCHS=2 \
XIANGQI_BATCH_SIZE=128 \
XIANGQI_NUM_WORKERS=0 \
XIANGQI_TRAIN_BATCH_LIMIT=20 \
XIANGQI_VAL_BATCH_LIMIT=10 \
../.venv/bin/python train.py
```

Kết quả mong đợi:
- File model: `models/checkpoints/best_model.pth`
- TensorBoard events: `models/runs/demo_train/`

### 3) Xem kết quả train trực quan
```bash
cd /Users/nguyenducgiabao/XiangQiChess_HCMUT/xiangqi-ai-project/models
../.venv/bin/tensorboard --logdir runs --port 6006 --host 0.0.0.0
```
Mở: http://localhost:6006/

## Test 1 — Headless match (khuyến nghị để đo định lượng)
### Mục đích
- Chạy nhiều ván tự động, không UI.
- Đo win-rate/draw-rate, lý do kết thúc, số plies, độ ổn định.

### Kịch bản đề xuất
- **B1 (baseline):** Dummy MLAgent (không model) vs Random
- **B2 (trained):** Trained MLAgent (có `best_model.pth`) vs Random
- (Tuỳ chọn) **B3:** Trained MLAgent vs SearchAgent (Easy/Medium/Hard) để test “độ khó”

### Lệnh chạy đề xuất (A/B test: trained vs dummy)
```bash
cd /Users/nguyenducgiabao/XiangQiChess_HCMUT/xiangqi-ai-project
.venv/bin/python - <<'PY'
import random
from pathlib import Path

from agents.ml_agent import MLAgent
from agents.random_agent import RandomAgent
from core.rules import Color
from game.game_loop import run_headless_game

model_path = Path('models/checkpoints/best_model.pth').resolve()

def run_series(label, agent_factory, games=10, max_turns=160, seed=2026):
    red_wins = black_wins = draws = 0
    for i in range(games):
        red_agent = agent_factory()
        black_agent = RandomAgent(player_id=Color.BLACK, rng=random.Random(seed + i))
        result = run_headless_game(red_agent, black_agent, max_turns=max_turns)
        winner = "draw" if result.winner is None else result.winner.value
        if winner == "red":
            red_wins += 1
        elif winner == "black":
            black_wins += 1
        else:
            draws += 1
        print(f"{label} game {i+1}: winner={winner} reason={result.reason} plies={len(result.history)}")
    print(f"{label} summary: red={red_wins} black={black_wins} draw={draws}")

run_series(
    "TRAINED",
    lambda: MLAgent(player_id=Color.RED, model_path=model_path, level="Hard"),
)
print("---")
run_series(
    "DUMMY",
    lambda: MLAgent(player_id=Color.RED, model_path=None, level="Hard"),
)
PY
```

### Metric cần ghi lại (tối thiểu)
- Win/Draw/Loss rate (vs Random và/hoặc vs Search).
- Tỉ lệ game kết thúc do:
  - `checkmate`
  - `stalemate`
  - `threefold_repetition`
  - `max_turns_reached`
- Số plies trung bình / game (độ “đi được lâu” và tốc độ kết thúc).
- Thời gian trung bình / game (performance).

## Test 2 — UI demo (khuyến nghị để trình diễn)
### Mục đích
- Cho thấy AI “biết đi” trong giao diện.
- Dễ demo trực quan (Human vs ML, ML vs Random).

### Chạy UI với model đã học
```bash
cd /Users/nguyenducgiabao/XiangQiChess_HCMUT/xiangqi-ai-project
XIANGQI_ML_MODEL_PATH=models/checkpoints/best_model.pth .venv/bin/python main.py
```

Trong menu:
- Chọn **Human vs ML** để người chơi đấu với AI học từ data.
- Chọn **ML vs Random** để xem AI tự chơi và quan sát hành vi.

## Kết luận demo mong đợi
- Có TensorBoard thể hiện loss/accuracy giảm/tăng theo epoch (bằng chứng “có học”).
- Có headless A/B test cho thấy trained model có hành vi khác baseline (ít lặp vô nghĩa hơn, hoặc kết quả vs Random tốt hơn).
- Có UI demo để người xem thấy AI đi nước cụ thể theo thời gian thực.
