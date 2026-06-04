# Hướng Dẫn Chạy Demo

## Yêu Cầu Cài Đặt

| Công cụ | Tải tại |
|---|---|
| Python 3.8+ | python.org |
| Git | git-scm.com |
| VS Code | code.visualstudio.com |

---

## Các Bước Thực Hiện

### 1. Clone project về máy

Mở **Terminal trong VS Code** (`Ctrl + `` ` ``), chọn **Command Prompt**, gõ:

```cmd
git clone https://github.com/DaoGiaPhuc/final-data-mining-project.git
cd final-data-mining-project
```

### 2. Cài thư viện

```cmd
pip install -r requirements.txt
```

### 3. Chạy app

```cmd
streamlit run app/app.py
```

Trình duyệt tự mở `http://localhost:8501` — nhấn ** StartDemo** là xong!

---

## Lưu Ý

- **Không tắt terminal** trong khi demo — app sẽ dừng ngay
- Để dừng app: nhấn `Ctrl + C` trong terminal
- Nếu trình duyệt không tự mở: copy `http://localhost:8501` vào Chrome

---

## Lỗi Thường Gặp

| Lỗi | Cách sửa |
|---|---|
| `git not recognized` | Cài Git tại git-scm.com, khởi động lại VS Code |
| `streamlit not recognized` | Chạy lại `pip install streamlit` |
| `File does not exist: app/app.py` | Kiểm tra đang đứng đúng thư mục gốc project |
| Trang trắng / không load | Chờ 5 giây rồi refresh trình duyệt |
