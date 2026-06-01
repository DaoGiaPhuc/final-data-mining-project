import os
import pandas as pd

# Đọc file final_sales vừa tạo từ bước tiền xử lý
df = pd.read_csv('data/processed/final_sales.csv')

print("--- THIẾT KẾ KHO DỮ LIỆU & OLAP VIEW ---")
os.makedirs('data/warehouse', exist_ok=True)

# 1. Tạo các bảng Dimension chuẩn chỉ
print("Dang tao cac bang chieu (Dim)...")

# dim_customer
dim_customer = df[['customer_id', 'customer_unique_id', 'customer_state']].drop_duplicates()
dim_customer.to_csv('data/warehouse/dim_customer.csv', index=False)

# dim_seller
dim_seller = df[['order_id', 'seller_state']].drop_duplicates() # Dùng order_id để lát tiện join với Fact
dim_seller.to_csv('data/warehouse/dim_seller.csv', index=False)

# dim_product_payment_time (Gộp chung các thuộc tính sản phẩm, thanh toán và tháng vào 1 bảng chiều để map theo order_id)
dim_info = df[['order_id', 'order_month', 'product_category_name', 'payment_type']].drop_duplicates()
dim_info.to_csv('data/warehouse/dim_info.csv', index=False)


# 2. Tạo bảng Fact Sales
print("Dang tao bang Fact_Sales...")
fact_sales = df[['order_id', 'customer_id', 'order_purchase_timestamp', 'price', 'freight_value', 'total_amount', 'review_score', 'delivery_days']].drop_duplicates()
fact_sales.to_csv('data/warehouse/fact_sales.csv', index=False)


# 3. TẠO FILE THEO YÊU CẦU MỚI: olap_sales_view.csv (Bằng cách join Fact với Dim)
print("Dang tao file olap_sales_view.csv bang cach join...")

# Thực hiện JOIN chuẩn chỉ: Lấy Fact_Sales join với các bảng Dimension qua các khóa tương ứng
olap_sales_view = fact_sales \
    .merge(dim_customer, on='customer_id', how='left') \
    .merge(dim_seller, on='order_id', how='left') \
    .merge(dim_info, on='order_id', how='left')

# Lọc đúng và đủ các cột tối thiểu anh Phúc cần (Đã bao gồm seller_state)
required_cols_olap = [
    'order_id', 'customer_unique_id', 'order_month', 'customer_state', 
    'product_category_name', 'payment_type', 'seller_state', 'total_amount', 'review_score', 'delivery_days'
]

# Xuất file hoàn chỉnh
olap_sales_view = olap_sales_view[required_cols_olap].drop_duplicates()
olap_sales_view.to_csv('data/warehouse/olap_sales_view.csv', index=False)

print("=> Da tao xong file data/warehouse/olap_sales_view.csv!")