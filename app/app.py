import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. CẤU HÌNH BAN ĐẦU GIAO DIỆN
st.set_page_config(page_title="Olist · Overview", page_icon="🛒", layout="wide")

# Áp dụng Dark Mode đồng bộ và tinh tế cho Dashboard
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0f1117; color: #e8e8e8; }
.dash-title { font-size: 2.4rem; font-weight: 700; color: #fff; margin: 0; }
.dash-subtitle { color: #888; font-size: 0.95rem; margin-top: 0.3rem; }
.section-title { font-size: 1.3rem; font-weight: 600; color: #fff; margin: 2rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid #2a2a3a; }
.kpi-card { background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 14px; padding: 1.4rem 1.6rem; position: relative; overflow: hidden; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:14px 14px 0 0; }
.kpi-card.green::before  { background: #00c07f; }
.kpi-card.blue::before   { background: #4e8ef7; }
.kpi-card.orange::before { background: #f79c4e; }
.kpi-card.purple::before { background: #a569f7; }
.kpi-label { font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:#666; margin-bottom:0.5rem; }
.kpi-value { font-size:2rem; font-weight: 700; color:#fff; line-height:1; }
.kpi-sub   { font-size:0.8rem; color:#555; margin-top:0.35rem; }
.algo-box { background: #1a1d27; border: 1px solid #2a2d3a; border-left: 4px solid #4e8ef7; border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1rem; font-size: 0.88rem; color: #bbb; line-height: 1.8; }
</style>
""", unsafe_allow_html=True)

# 2. HÀM NẠP KHO DỮ LIỆU ĐÃ QUY HOẠCH ĐƯỜNG DẪN
@st.cache_data
def load_data():
    # Đọc dữ liệu từ các thư mục cấu trúc mới
    sales     = pd.read_csv("data/processed/final_sales.csv")
    fact      = pd.read_csv("data/warehouse/fact_sales.csv")
    dim_prod  = pd.read_csv("data/warehouse/dim_product.csv")
    clusters  = pd.read_csv("outputs/customer_clusters.csv")  
    cube_df   = pd.read_csv("outputs/iceberg_cube.csv")       

    # Định dạng tiền xử lý dữ liệu phục vụ biểu đồ thời gian
    sales["order_purchase_timestamp"] = pd.to_datetime(sales["order_purchase_timestamp"])
    sales["category_clean"] = sales["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    
    # Đồng bộ thông tin bảng Fact
    fact = fact.merge(dim_prod, on="product_id", how="left")
    fact["category_clean"] = fact["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    
    return sales, fact, clusters, cube_df

# Kiểm tra sự tồn tại của tệp tin kho dữ liệu
try:
    df, fact, clusters, cube_df = load_data()
except FileNotFoundError as e:
    st.error(f" Thiếu tệp tin dữ liệu hoặc cấu trúc thư mục không đúng: {e}")
    st.stop()

# Lấy tập dữ liệu đơn hàng duy nhất phục vụ tính toán chỉ số tổng
orders_df = df.drop_duplicates("order_id")

# HEADER ỨNG DỤNG
st.markdown("""
<div style="padding:1.5rem 0 1rem 0; border-bottom:1px solid #2a2a3a; margin-bottom:1.5rem;">
    <div class="dash-title">🛒 Olist E-Commerce Advanced Analytics Dashboard</div>
    <div class="dash-subtitle">Brazilian E-Commerce · Khai phá dữ liệu & Phân tích thông minh</div>
</div>
""", unsafe_allow_html=True)

# 3. KPI SECTION — ĐÃ SỬA CÔNG THỨC THEO YÊU CẦU
# Tính total_revenue bằng cách groupby('order_id') lấy giá trị đơn hàng gốc (first), sau đó tính tổng (sum)
total_revenue   = orders_df.groupby("order_id")["total_amount"].first().sum()
total_orders    = orders_df["order_id"].nunique()
total_customers = df["customer_unique_id"].nunique()
avg_order_value = total_revenue / total_orders

def kpi(col, color, label, value, sub):
    col.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
kpi(c1, "green", "Tổng Doanh Thu", f"R$ {total_revenue/1e6:.2f}M", "Tích hợp giá trị đơn gốc")
kpi(c2, "blue", "Số Đơn Hàng", f"{total_orders:,}", "Mã đơn hàng duy nhất")
kpi(c3, "orange", "Số Khách Hàng", f"{total_customers:,}", "Khách hàng duy nhất")
kpi(c4, "purple", "AOV", f"R$ {avg_order_value:.2f}", "Doanh thu trung bình / Đơn")

# 4. BIỂU ĐỒ DOANH THU THEO THÁNG
st.markdown('<div class="section-title"> Doanh Thu Qua Các Tháng</div>', unsafe_allow_html=True)
monthly = (orders_df.groupby("order_month")["total_amount"].sum()
           .reset_index().rename(columns={"order_month":"Tháng","total_amount":"Doanh Thu (R$)"}))
monthly = monthly[monthly["Tháng"].between("2017-01", "2018-08")].sort_values("Tháng")

fig_line = px.area(monthly, x="Tháng", y="Doanh Thu (R$)", color_discrete_sequence=["#00c07f"], template="plotly_dark")
fig_line.update_traces(fill="tozeroy", fillcolor="rgba(0,192,127,0.12)", line=dict(width=2.5))
fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)", margin=dict(l=0,r=0,t=10,b=0), xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"), height=260)
st.plotly_chart(fig_line, use_container_width=True)

# 5. KHAI PHÁ DOANH THU: TOP NGÀNH HÀNG VÀ ĐỊA LÝ
col_l, col_r = st.columns(2)
with col_l:
    st.markdown('<div class="section-title"> Top 10 Ngành Hàng Bán Chạy</div>', unsafe_allow_html=True)
    cat = (df.drop_duplicates(["order_id","product_category_name"]).groupby("category_clean")["order_id"].count().nlargest(10).reset_index().rename(columns={"category_clean":"Ngành hàng","order_id":"Số Đơn"}).sort_values("Số Đơn"))
    fig_cat = px.bar(cat, x="Số Đơn", y="Ngành hàng", orientation="h", color="Số Đơn", color_continuous_scale=["#1a3a5c","#4e8ef7"], template="plotly_dark")
    fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)", margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False, yaxis=dict(showgrid=False), xaxis=dict(gridcolor="#1f2230"), height=340)
    st.plotly_chart(fig_cat, use_container_width=True)

with col_r:
    st.markdown('<div class="section-title"> Mật Độ Đơn Hàng Theo Các Bang</div>', unsafe_allow_html=True)
    state = (orders_df.groupby("customer_state")["order_id"].count().reset_index().rename(columns={"customer_state":"Bang","order_id":"Số Đơn"}).sort_values("Số Đơn", ascending=False).head(12))
    fig_state = px.bar(state, x="Bang", y="Số Đơn", color="Số Đơn", color_continuous_scale=["#2a1a3a","#a569f7"], template="plotly_dark")
    fig_state.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)", margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False, xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"), height=340)
    st.plotly_chart(fig_state, use_container_width=True)

# 6. ĐỌC KẾT QUẢ TOP-DOWN ICEBERG CUBE
st.markdown('<div class="section-title"> Iceberg Cube — Kết Quả Thuật Toán BUC</div>', unsafe_allow_html=True)
st.markdown("""<div class="algo-box"><b>Cắt tỉa nâng cao (BUC Top-Down Pruning):</b> Dữ liệu hiển thị bảng phân tích đa chiều được đọc trực tiếp từ tệp lưu trữ kết quả tính toán sẵn <code>outputs/iceberg_cube.csv</code>, tự động loại trừ các phần tử không đạt ngưỡng Min Support.</div>""", unsafe_allow_html=True)

top10_cube = cube_df[cube_df["cuboid"] != "ALL*"].nlargest(10, "order_count").copy()
st.dataframe(top10_cube, use_container_width=True, hide_index=True)

# 7. ĐỌC KẾT QUẢ CUSTOMER CLUSTERING
st.markdown('<div class="section-title">👥 Mô Hình Phân Cụm Khách Hàng (RFM + K-Means)</div>', unsafe_allow_html=True)
CLUSTER_COLORS = {"Khách hàng tiềm năng": "#4e8ef7", "Khách hàng giá trị thấp": "#f79c4e", "Khách hàng giá trị cao": "#00c07f", "Khách hàng ít hoạt động": "#a569f7"}

# Lấy mẫu ngẫu nhiên cố định để tối ưu hóa hiệu năng render đồ thị
sample_cls = clusters.sample(min(3000, len(clusters)), random_state=42)
fig_scatter = px.scatter(sample_cls, x="pca_1", y="pca_2", color="cluster_name", color_discrete_map=CLUSTER_COLORS, template="plotly_dark", opacity=0.6, labels={"pca_1":"Tọa độ PCA 1","pca_2":"Tọa độ PCA 2","cluster_name":"Phân loại nhóm"})
fig_scatter.update_traces(marker=dict(size=4.5))
fig_scatter.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)", margin=dict(l=0,r=0,t=15,b=0), height=380, xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
st.plotly_chart(fig_scatter, use_container_width=True)

# FOOTER DƯỚI CÙNG
st.markdown("""<hr style="border-color:#2a2a3a; margin-top:2rem;"><p style="text-align:center; color:#444; font-size:0.8rem;">Data Mining Project · Olist Brazilian E-Commerce Dashboard</p>""", unsafe_allow_html=True)
