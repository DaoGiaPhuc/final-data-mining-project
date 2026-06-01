import os
import pandas as pd

print("--- TIẾN HÀNH TIỀN XỬ LÝ DỮ LIỆU OLIST ---")
# 1. Đọc tất cả các file dữ liệu gốc cần thiết
orders = pd.read_csv('olist_orders_dataset.csv')
order_items = pd.read_csv('olist_order_items_dataset.csv')
customers = pd.read_csv('olist_customers_dataset.csv')
products = pd.read_csv('olist_products_dataset.csv')
sellers = pd.read_csv('olist_sellers_dataset.csv')
payments = pd.read_csv('olist_order_payments_dataset.csv')
reviews = pd.read_csv('olist_order_reviews_dataset.csv') # <--- ĐỌC THÊM REVIEW

# 2. Hợp nhất các bảng dữ liệu (Merge dữ liệu)
print("Dang merge cac bang du lieu goc...")
df = pd.merge(orders, customers, on='customer_id', how='inner')
df = pd.merge(df, order_items, on='order_id', how='inner')
df = pd.merge(df, products, on='product_id', how='left')
df = pd.merge(df, sellers, on='seller_id', how='left')
df = pd.merge(df, payments, on='order_id', how='left')
df = pd.merge(df, reviews, on='order_id', how='left') # <--- MERGE THÊM REVIEW

# 3. Làm sạch và Chuẩn hóa ngày tháng
print("Dang xu ly định dang ngay thang...")
datetime_cols = [
    'order_purchase_timestamp', 'order_approved_at', 
    'order_delivered_carrier_date', 'order_delivered_customer_date', 'order_estimated_delivery_date'
]
for col in datetime_cols:
    df[col] = pd.to_datetime(df[col])

# Xóa dữ liệu trùng lặp
df = df.drop_duplicates()

# 4. Kỹ nghệ đặc trưng (Tính toán biến mới theo yêu cầu anh Phúc)
print("Dang tinh toan cac bien moi...")
# Đổi tên biến doanh thu thành total_amount theo yêu cầu
df['total_amount'] = df['price'] + df['freight_value']

# Tính số ngày giao hàng thực tế
df['delivery_days'] = (df['order_delivered_customer_date'] - df['order_delivered_carrier_date']).dt.days

# Trích xuất tháng mua hàng (Dạng YYYY-MM) để khớp cột order_month
df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)

# 5. Xuất file final_sales.csv kiểm tra đủ các cột tối thiểu của anh Phúc
required_cols_final = [
    'order_id', 'customer_id', 'customer_unique_id', 'order_purchase_timestamp', 
    'order_month', 'customer_state', 'seller_state', 'product_category_name', 'payment_type', # <--- ĐÃ THÊM 'seller_state' VÀO ĐÂY
    'price', 'freight_value', 'total_amount', 'review_score', 'delivery_days'
]
# Giữ lại các cột cần thiết và xuất file
final_sales = df[required_cols_final].copy()

os.makedirs('data/processed', exist_ok=True)
final_sales.to_csv('data/processed/final_sales.csv', index=False)
print("=> Da tao xong file data/processed/final_sales.csv!")