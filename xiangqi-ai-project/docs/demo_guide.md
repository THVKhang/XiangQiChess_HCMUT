# Demo Guide — XiangQi Chess AI (HCMUT Assignment 3)

Hướng dẫn này dành cho **Khang** để quay demo project.  

---

## Mục lục

1. [Chuẩn bị môi trường](#1-chuẩn-bị-môi-trường)
2. [Khởi động game](#2-khởi-động-game)
3. [Demo từng mode chơi](#3-demo-từng-mode-chơi)
   - 3.1 Human vs AI
   - 3.2 Human vs ML (ML Agent Level)
   - 3.3 AI vs AI
   - 3.4 ML vs Random
   - 3.5 ML vs Search (ML Agent vs Minimax)
4. [Demo headless simulation (terminal)](#4-demo-headless-simulation-terminal)
5. [Thứ tự quay khuyến nghị](#5-thứ-tự-quay-khuyến-nghị)
6. [Checklist trước khi quay](#6-checklist-trước-khi-quay)

---

## 1. Chuẩn bị môi trường

### 1.1 Kiểm tra Python

Mở **PowerShell** (hoặc CMD), chạy:

```powershell
python --version
```

Cần Python **3.10** trở lên.

### 1.2 Cài dependencies

Từ thư mục gốc của project, chạy:

```powershell
pip install pygame numpy
```

> **Nếu đã cài rồi:** lệnh trên sẽ báo "already satisfied", bỏ qua.

Kiểm tra nhanh:

```powershell
python -c "import pygame; import numpy; print('OK')"
```

Nếu in ra `OK` là đủ để chạy game.

### 1.3 Vào đúng thư mục

```powershell
cd "d:\a_intro_to_ai\ASS3\XiangQiChess_HCMUT\xiangqi-ai-project"
```

> **Lưu ý:** Tất cả lệnh `python` trong guide này đều chạy từ thư mục `xiangqi-ai-project/`.

---

## 2. Khởi động game

```powershell
python main.py
```

Một cửa sổ Pygame hiện ra — đây là **Menu** chính.

**Giao diện Menu gồm:**
- Cột trái: 3 mode cơ bản (Human vs AI, Human vs ML, AI vs AI)
- Cột phải: 3 mode mới (AI vs Random, ML vs Random, ML vs Search)
- Phần dưới: Level selector (thay đổi theo mode đang chọn)
- Nút **Start** (xanh lá) và **Quit** (đỏ)

---

## 3. Demo từng mode chơi

---

### 3.1 Human vs AI

**Mục đích:** Chứng minh game chạy ổn định, luật cờ đúng, AI phản hồi.

**Các bước:**

1. Click **"Human vs AI"** ở menu.
2. Chọn level AI: **Easy** (cho demo ngắn) hoặc **Hard** (cho demo thuyết phục).
3. Click **Start**.
4. Bàn cờ hiện ra — quân Đỏ là Human (dưới), quân Đen là AI (trên).
5. **Thực hiện 3–5 nước đi** (click vào quân muốn đi → click ô đích):
   - Ô được chọn sẽ highlight.
   - Nước đi hợp lệ được chấp nhận ngay.
   - Nước đi bất hợp lệ bị bỏ qua (không crash).
6. AI tự đánh sau mỗi lượt của mình.
7. Status bar (dưới cùng) hiện tên quân AI vừa đi và tọa độ nước đi.

**Điểm cần quay rõ:**
- Highlight ô khi click.
- AI tự phản hồi trong ~0.3 giây.
- Status bar cập nhật.

---

### 3.2 Human vs ML (ML Agent + Level Selector)

**Mục đích:** Thể hiện ML Agent đã tích hợp vào game loop, Level selector hoạt động.

**Các bước — lần 1 (Easy):**

1. Click **"Human vs ML"** ở menu.
2. Panel level đổi thành **"ML Agent Level"** (xanh dương).
3. Click **Easy**.
4. Click **Start**.
5. Đánh 4–5 nước. Để ý ML Agent (Đen) đôi khi đi **ngẫu nhiên** (vì epsilon=0.4).
6. Nhấn nút **Back** để về menu.

**Các bước — lần 2 (Hard):**

1. Chọn lại **"Human vs ML"**.
2. Click **Hard**.
3. Click **Start**.
4. Quan sát ML Agent bây giờ đi **nhất quán hơn** (argmax policy, có anti-repetition).
5. Thử để game chạy đến cuối (hoặc nhấn **Quit** sau ~10 nước).

**Điểm cần quay rõ:**
- Panel level đổi khi click "Human vs ML" (khác với Human vs AI).
- Label **"ML Agent Level"** màu xanh dương hiện ra.
- Sự khác biệt hành vi Easy vs Hard (Easy đôi khi đi lạ).

---

### 3.3 AI vs AI

**Mục đích:** Thể hiện hai Search Agent tự đấu nhau, level độc lập cho mỗi bên.

**Các bước:**

1. Click **"AI vs AI"**.
2. Panel level đổi thành hai cột: **"Red AI"** và **"Black AI"**.
3. Set Red = **Easy**, Black = **Hard** (để thấy chênh lệch rõ).
4. Click **Start**.
5. Để game chạy ~15–20 nước (hoặc đến khi có người thắng).
6. Status bar hiện tên agent và nước đi mỗi lượt.

**Điểm cần quay rõ:**
- Hai cột level selector riêng biệt.
- Cả hai bên AI tự đánh liên tục.
- Game kết thúc với overlay "RED WINS" / "BLACK WINS" / "DRAW".

---

### 3.4 ML vs Random

**Mục đích:** Thể hiện ML Agent đấu với Random Agent baseline.

**Các bước:**

1. Click **"ML vs Random"**.
2. Panel level: chọn **Hard** cho ML Agent.
3. Click **Start**.
4. Để game chạy hết (Random Agent thường thua nhanh hơn AI).
5. Quan sát game over overlay.

**Điểm cần quay rõ:**
- ML Agent (Đỏ) đi theo strategy rõ ràng; Random Agent (Đen) đi ngẫu nhiên.
- Game thường kết thúc trong 30–60 nước.

---

### 3.5 ML vs Search (ML Agent vs Minimax)

**Mục đích:** Thể hiện mode mới nhất — ML Agent đấu với Search Agent, cả hai level độc lập.

**Các bước:**

1. Click **"ML vs Search"**.
2. Panel level: **hai selector xuất hiện side-by-side**:
   - Trái: **ML Level** → chọn **Hard**
   - Phải: **AI Level** → chọn **Easy**
3. Click **Start**.
4. Để game chạy ~20 nước.
5. Nhấn **New Game** (nếu muốn chạy thêm lần nữa với Hard vs Hard).

**Điểm cần quay rõ:**
- Hai panel level song song (đây là điểm khác biệt duy nhất trong menu).
- Label "ML Level" màu xanh dương / "AI Level" màu tối.
- Cả hai agent tự đánh.

---

## 4. Demo headless simulation (terminal)

**Mục đích:** Thể hiện khả năng chạy giả lập ẩn (không cần UI) để đánh giá AI.

Mở **terminal mới** (PowerShell), `cd` vào `xiangqi-ai-project/`.

### 4.1 ML vs Random (10 ván)

```powershell
python evaluation/headless_match.py --mode ml-vs-random --games 10 --ml-level Hard
```

Output mẫu:
```
=== Headless ML vs Random Summary ===
Total games : 10
ML/red wins :  3
Random wins :  2
Draws       :  5
Avg time    : 3500.0 ms/game
```

### 4.2 ML vs Minimax (5 ván, Easy Minimax)

```powershell
python evaluation/headless_match.py `
  --mode ml-vs-search `
  --games 5 --max-turns 160 `
  --ml-level Hard `
  --search-level Easy `
  --search-algorithm minimax
```

### 4.3 Xuất kết quả ra JSON

```powershell
python evaluation/headless_match.py `
  --mode ml-vs-search --games 5 `
  --ml-level Hard --search-level Easy `
  --json-out evaluation/results/ml_vs_minimax_demo.json
```

Sau đó mở file JSON để show kết quả chi tiết.

> **Lưu ý khi quay:** Giữ terminal đủ to để thấy output. Chạy lệnh ngắn trước để check, sau mới quay màn hình.

---

## 5. Thứ tự quay khuyến nghị

| # | Cảnh | Thời lượng gợi ý |
|---|------|-----------------|
| 1 | Chạy `python main.py`, menu hiện ra | 15 giây |
| 2 | Click các mode, thấy panel level thay đổi | 20 giây |
| 3 | **Human vs AI** — đánh vài nước | 45 giây |
| 4 | **Human vs ML Easy** → Back → **Human vs ML Hard** | 60 giây |
| 5 | **ML vs Search** — show hai panel level song song, để game chạy | 45 giây |
| 6 | **AI vs AI** — để game chạy đến kết thúc, show overlay | 60 giây |
| 7 | Terminal: chạy headless ML vs Random | 20 giây |
| 8 | Terminal: chạy headless ML vs Minimax + show JSON output | 30 giây |

**Tổng ước tính: ~5 phút**

---

## 6. Checklist trước khi quay

- [ ] `pip install pygame numpy` đã chạy thành công
- [ ] `python -c "import pygame; import numpy; print('OK')"` in ra `OK`
- [ ] `cd xiangqi-ai-project` đúng thư mục
- [ ] `python main.py` mở được cửa sổ game
- [ ] Cửa sổ game đủ to (kéo rộng để thấy rõ bàn cờ)
- [ ] Terminal song song bên cạnh (cho phần headless)
- [ ] Tắt thông báo máy tính, không bị interrupt khi quay
- [ ] Thử chạy thử một lần từ đầu đến cuối trước khi bấm record

---

*Hỏi Nhi nếu có vấn đề gì khi chạy.*
