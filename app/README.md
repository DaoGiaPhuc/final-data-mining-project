#  Olist E-Commerce Advanced Analytics Dashboard

Ứng dụng Dashboard phân tích nâng cao cho dữ liệu thương mại điện tử Olist (Brazil), tích hợp kết quả từ các thuật toán Khai phá dữ liệu (**Data Mining**) và Học máy (**Machine Learning**). Hệ thống được triển khai trên nền tảng **Google Colab** và đóng gói giao diện bằng **Streamlit**, kết nối ra internet thông qua **Ngrok Tunnel**.

---

##  Kiến Trúc Vận Hành Hệ Thống

Dự án hoạt động dựa trên luồng xử lý và kết nối khép kín từ lưu trữ dữ liệu đến giao diện tương tác người dùng:

Trước khi vận hành, toàn bộ 6 file dữ liệu đầu ra của quá trình Mining cần được nạp chính xác vào hệ thống thư mục ảo của Google Colab theo sơ đồ sau:

```text
📂 data/
 ├── 📂 processed/
 │    └── 📄 final_sales.csv            # Dữ liệu tích hợp tổng hợp cuối cùng
 └── 📂 warehouse/
      ├── 📄 fact_sales.csv             # Bảng sự kiện (Fact Table)
      ├── 📄 dim_product.csv            # Bảng danh mục sản phẩm (Dimension Table)
      ├── 📄 dim_date.csv               # Bảng thời gian (Dimension Table)
      ├── 📄 dim_payment.csv            # Bảng phương thức thanh toán (Dimension Table)
      └── 📄 customer_clusters.csv      # Kết quả phân cụm khách hàng (RFM + K-Means)'''
```

###
Bước 1: Thiết lập môi trường & Tạo thư mục
Chạy ô mã nguồn để cài đặt các thư viện lõi và khởi tạo cấu trúc thư mục lưu trữ:
```python
!pip install streamlit plotly pandas pyngrok -q

import os
os.makedirs("data/processed", exist_ok=True)
os.makedirs("data/warehouse", exist_ok=True)
print(" Khởi tạo cấu trúc Data Warehouse thành công!")
``` 

### Bước 2: Nạp dữ liệu đầu vào (Upload Files)
Do việc upload nhiều file dung lượng lớn cùng lúc dễ gây nghẽn mạng trên Colab, bạn hãy chia nhỏ ra và tải lên lần lượt theo cấu trúc ngăn chứa sau:

Thư mục thứ nhất (data/processed): Chứa file tổng hợp cuối cùng.

File 1: final_sales.csv

Thư mục thứ hai (data/warehouse): Chứa các file Fact, Dimension và kết quả thuật toán nâng cao.

File 2: fact_sales.csv

File 3: dim_product.csv

File 4: dim_date.csv

File 5: dim_payment.csv

File 6: customer_clusters.csv (Kết quả mô hình K-Means)

Lưu ý quan trọng khi chọn file: Code đã tích hợp tính năng tự động đổi tên file. Kể cả khi file bạn tải về máy bị dính các ký tự lạ như final_sales (1).csv hay fact_sales(2).csv, hệ thống vẫn tự nhận diện đúng và đưa về tên gốc chuẩn xác.

### BƯỚC 3: Tạo File Giao Diện Ứng Dụng (overview.py)
Tạo một ô code mới, sao chép toàn bộ mã nguồn giao diện Dashboard nâng cao (có chứa biểu đồ Phân cụm khách hàng Radar, biểu đồ nhánh Khối lập phương Iceberg Cube, mô hình phân bố địa lý) rồi bấm Run.

Dòng mã ```%%writefile overview.py``` ở đầu ô code sẽ tự động đóng gói toàn bộ đoạn code bên dưới thành một file chạy duy nhất trong bộ nhớ Colab.

### BƯỚC 4: Thiết lập Khóa xác thực (Ngrok Token)
Để đưa ứng dụng từ môi trường ảo của Google Colab ra một đường link Internet công cộng, bạn cần sử dụng dịch vụ Ngrok làm cầu nối.
Tạo ô code mới, thay mã Token cá nhân của bạn vào và bấm Run:

```Python
from pyngrok import ngrok
# Khóa token kết nối tài khoản cá nhân của bạn
ngrok.set_auth_token("3EYtWjfOp6UyV90Cxg76Ilu4xOK_5sUskGdnap19HfLEviX14")
print(" Đã cấu hình khóa xác thực thành công!")
```

### BƯỚC 5: Khởi chạy Máy chủ và Lấy link Dashboard
Đây là bước cuối cùng để kích hoạt toàn bộ hệ thống. Hãy tạo một ô code riêng biệt, dán đoạn mã điều phối luồng phụ này vào và bấm Run:

```Python
import subprocess
import threading
import time
from pyngrok import ngrok

# 1. Tắt bỏ tất cả tiến trình tunnel cũ đang chạy ngầm để tránh trùng cổng mạng (Port 8501)
ngrok.kill()

# 2. Định nghĩa hàm chạy Streamlit ở chế độ không giao diện (headless) trên cổng 8501
def run_streamlit():
    subprocess.run(["streamlit", "run", "overview.py",
                    "--server.port", "8501",
                    "--server.headless", "true"])

# 3. Kích hoạt luồng chạy ngầm (Daemon Thread) giúp Streamlit hoạt động liên tục mà không làm đơ trang Colab
threading.Thread(target=run_streamlit, daemon=True).start()
print(" Đang khởi tạo máy chủ ứng dụng Streamlit...")
time.sleep(5)  # Chờ 5 giây để hệ thống đọc và tính toán trước tập dữ liệu lớn

# 4. Mở cổng kết nối Ngrok ra Internet toàn cầu
public_url = ngrok.connect(8501)
print(f"link: {public_url.public_url}")
```

### HƯỚNG DẪN XỬ LÝ LỖI NHANH (Troubleshooting)
Lỗi Giao diện báo "FileNotFoundError": * Nguyên nhân: Do bạn chưa upload đủ 6 file dữ liệu hoặc đặt sai vị trí thư mục.
Khắc phục: Kiểm tra lại tab quản lý file bên góc trái màn hình Colab, đảm bảo các file nằm đúng vị trí trong data/processed và data/warehouse.
Lỗi "Đường link Ngrok không thể kết nối (404/ERR_CONNECTION)":
Nguyên nhân: Do tiến trình Streamlit cũ chưa được giải phóng hoặc Token bị hết hạn lưu lượng.
Khắc phục: Chỉ cần bấm chạy lại Bước 5, code đã có lệnh ngrok.kill() tự động dọn dẹp bộ nhớ cổng mạng và tạo cho bạn một đường link mới hoàn toàn sạch sẽ.
