import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json

st.set_page_config(page_title="Olist E-Commerce Analytics", page_icon="🛒", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f8f9fa; color: #212529; }
.main-title { font-size: 1.8rem; font-weight: 700; color: #1f2937; margin-bottom: 0px; }
.sub-title { font-size: 0.95rem; color: #6b7280; margin-bottom: 15px; }

/* CĂN GIỮA VÀ TỐI ƯU CÁC TABS */
.stTabs [data-baseweb="tab-list"] { 
    gap: 4px; 
    justify-content: center; /* Thêm dòng này để đưa toàn bộ hàng tab ra giữa */
}

.stTabs [data-baseweb="tab"] { 
    height: 45px; 
    padding: 0 15px; 
    background-color: #ffffff; 
    border-radius: 6px 6px 0 0; 
    border: 1px solid #e5e7eb; 
    border-bottom: none; 
    font-size: 0.9rem;
}

.stTabs [aria-selected="true"] { 
    background-color: #eff6ff; 
    border-top: 3px solid #3b82f6; 
    font-weight: 600; 
    color: #1d4ed8; 
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title" style="text-align: center;"> Olist E-Commerce Analytics Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title" style="text-align: center;">Hệ thống Khai phá Dữ liệu Toàn diện: Data Mining & Phân tích Hành vi</div>', unsafe_allow_html=True)

def resolve_path(relative_path):
    if os.path.exists(relative_path): return relative_path
    fallback = os.path.join("..", relative_path)
    if os.path.exists(fallback): return fallback
    return relative_path

@st.cache_data
def load_data():
    df       = pd.read_csv(resolve_path("data/processed/final_sales.csv"))
    fact     = pd.read_csv(resolve_path("data/warehouse/fact_sales.csv"))
    dim_prod = pd.read_csv(resolve_path("data/warehouse/dim_product.csv"))
    dim_date = pd.read_csv(resolve_path("data/warehouse/dim_date.csv"))
    clusters = pd.read_csv(resolve_path("outputs/customer_clusters.csv"))

    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_month"]    = df["order_month"].astype(str)
    df["category_clean"] = df["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    df["payment_type"]   = df["payment_type"].fillna("unknown")

    fact = fact.merge(dim_prod, on="product_id", how="left")
    fact["category_clean"] = fact["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    state_map = df[["customer_id","customer_state"]].drop_duplicates("customer_id")
    fact = fact.merge(state_map, on="customer_id", how="left")
    fact["customer_state"] = fact["customer_state"].fillna("unknown")
    fact["payment_type"]   = fact["payment_type"].fillna("unknown")

    return df, fact, dim_date, clusters

@st.cache_data
def load_cube():
    path = resolve_path("outputs/iceberg_cube.csv")
    if not (os.path.exists(path) and os.path.getsize(path) > 0): return pd.DataFrame(), False
    raw = pd.read_csv(path)
    DIM_COLS = {"order_month": "Month", "customer_state": "State", "product_category_name": "Category", "payment_type": "Payment"}
    raw["cuboid"] = raw.apply(lambda row: "ALL*" if not [lbl for col, lbl in DIM_COLS.items() if str(row[col]).upper() != "ALL"] else " × ".join([lbl for col, lbl in DIM_COLS.items() if str(row[col]).upper() != "ALL"]), axis=1)
    raw["label"] = raw.apply(lambda row: " | ".join([str(row[col]) for col in DIM_COLS if str(row[col]).upper() != "ALL"]) or "ALL*", axis=1)
    raw["total_revenue"] = raw["total_sales"]
    return raw, True

@st.cache_data
def load_metrics():
    path = resolve_path("outputs/model_metrics.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f: return json.load(f)
    return {}

try:
    df, fact, dim_date, clusters = load_data()
    cube_df, cube_loaded = load_cube()
    metrics = load_metrics()
except FileNotFoundError as e:
    st.error(f" Lỗi đọc file. Vui lòng kiểm tra lại cấu trúc: {e}")
    st.stop()

orders = df.groupby("order_id").agg(
    total_amount       = ("total_amount", "sum"),
    customer_unique_id = ("customer_unique_id", "first"),
    order_month        = ("order_month", "first"),
    payment_type       = ("payment_type", "first"),
).reset_index()

TOTAL_REVENUE   = orders["total_amount"].sum()
TOTAL_ORDERS    = len(orders)
TOTAL_CUSTOMERS = orders["customer_unique_id"].nunique()
AOV             = TOTAL_REVENUE / TOTAL_ORDERS


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    " 1. Overview", 
    " 2. EDA", 
    " 3. Warehouse", 
    " 4. Iceberg Cube", 
    " 5. Clustering",
    " 6. Actions"
])

# TAB 1: OVERVIEW (Tổng quan KPI)
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng Doanh Thu", f"R$ {TOTAL_REVENUE/1e6:.2f}M", "Sum(total_amount) / order")
    c2.metric("Số Đơn Hàng (Unique)", f"{TOTAL_ORDERS:,}")
    c3.metric("Số Khách Hàng", f"{TOTAL_CUSTOMERS:,}")
    c4.metric("Giá Trị Đơn Trung Bình (AOV)", f"R$ {AOV:.0f}")

    monthly = orders.groupby("order_month")["total_amount"].sum().reset_index().rename(columns={"order_month":"Tháng", "total_amount":"Doanh Thu"}).sort_values("Tháng")
    monthly = monthly[monthly["Tháng"].between("2017-01", "2018-08")]
    fig_line = px.area(monthly, x="Tháng", y="Doanh Thu", template="plotly_white", color_discrete_sequence=["#3b82f6"], title="Biểu đồ Doanh Thu Theo Tháng")
    fig_line.update_traces(fill="tozeroy", fillcolor="rgba(59, 130, 246, 0.15)")
    fig_line.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_line, use_container_width=True)

# TAB 2: EDA (Phân phối dữ liệu)
with tab2:
    col1, col2 = st.columns(2)
    with col1:
        pay = orders.groupby("payment_type")["order_id"].count().reset_index().rename(columns={"payment_type":"Loại", "order_id":"Đơn"})
        fig_pie = px.pie(pay, values="Đơn", names="Loại", hole=0.45, template="plotly_white", color_discrete_sequence=["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6"], title="Phương Thức Thanh Toán")
        fig_pie.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        cat = df.drop_duplicates(["order_id","product_category_name"]).groupby("category_clean")["order_id"].count().nlargest(10).reset_index().sort_values("order_id")
        fig_bar = px.bar(cat, x="order_id", y="category_clean", orientation="h", template="plotly_white", color_discrete_sequence=["#3b82f6"], title="Top 10 Ngành Hàng (Lượng Đơn)")
        fig_bar.update_layout(height=350, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)

# TAB 3: DATA WAREHOUSE
with tab3:
    st.info(" **Kiến trúc Star Schema:** Dữ liệu chuẩn hóa 1 Fact Table trung tâm và các Dimension Tables vệ tinh.")
    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.markdown("** Fact Table (fact_sales)**")
        st.dataframe(fact.head(8), use_container_width=True, hide_index=True)
    with col_w2:
        st.markdown("** Dim Table (dim_date)**")
        st.dataframe(dim_date.head(8), use_container_width=True, hide_index=True)

# TAB 4: ICEBERG CUBE (Thuật toán BUC)
with tab4:
    if not cube_loaded:
        st.warning(" Không tìm thấy kết quả tính toán Iceberg Cube.")
    else:
        MIN_SUP = int(cube_df["support_count"].min())
        st.success(f"**Min Support: {MIN_SUP} đơn**. Tự động cắt tỉa các cell không đạt.")
        
        st.markdown("**Top 10 Đới Dữ Liệu Tốt Nhất (Iceberg Result)**")
        top10 = cube_df[cube_df["cuboid_level"]>0].nlargest(10, "order_count")[["cuboid", "label", "order_count", "total_revenue"]].copy()
        top10["total_revenue"] = top10["total_revenue"].map("R$ {:,.0f}".format)
        top10.columns = ["Cuboid Level", "Tổ hợp giá trị (Cell)", "Số đơn", "Doanh thu"]
        st.dataframe(top10, use_container_width=True, hide_index=True)

# TAB 5: CLUSTERING (K-MEANS & PCA)
with tab5:
    CLUSTER_COLORS = {"Khách hàng tiềm năng": "#3b82f6", "Khách hàng giá trị thấp": "#f59e0b", "Khách hàng giá trị cao": "#10b981", "Khách hàng ít hoạt động": "#8b5cf6"}
    sil = metrics.get("silhouette_score", 0.45)
    st.info(f" **Mô hình Machine Learning:** Phân cụm khách hàng dựa trên chỉ số RFM (giảm chiều qua PCA). Silhouette Score: **{sil:.4f}**")

    sample = clusters.sample(min(4000, len(clusters)), random_state=42)
    fig_sc = px.scatter(sample, x="pca_1", y="pca_2", color="cluster_name", color_discrete_map=CLUSTER_COLORS, template="plotly_white", opacity=0.6, title="Biểu đồ phân bổ Scatter (PCA 2D)")
    fig_sc.update_traces(marker=dict(size=5))
    fig_sc.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False))
    st.plotly_chart(fig_sc, use_container_width=True)

# TAB 6: BUSINESS ACTIONS
with tab6:
    st.markdown("**Đặc điểm từng Cụm (Cluster Profile)**")
    profile = clusters.groupby("cluster_name").agg(
        Số_khách = ("customer_unique_id", "count"),
        R_Days = ("recency", "mean"),
        F_Orders = ("frequency", "mean"),
        M_Spend = ("monetary", "mean"),
    ).round(1).reset_index()
    profile = profile.rename(columns={"cluster_name": "Nhãn Cụm", "Số_khách": "SL Khách"})
    st.dataframe(profile.style.format({"R_Days": "{:.1f}", "F_Orders": "{:.1f}", "M_Spend": "R$ {:,.1f}"}).background_gradient(subset=["M_Spend"], cmap="Greens"), use_container_width=True, hide_index=True)

    st.markdown("#### Gợi ý chiến lược")
    c_rec1, c_rec2 = st.columns(2)
    with c_rec1:
        st.success("**Khách hàng giá trị cao:** Ưu tiên giữ chân — Loyalty program, gửi đặc quyền VIP.")
        st.info("**Khách hàng tiềm năng:** Nurture — Gợi ý sản phẩm liên quan (Cross-sell) kích thích mua lần 2.")
    with c_rec2:
        st.warning("**Khách hàng giá trị thấp:** Upsell — Bán theo combo hoặc Freeship khi đạt ngưỡng chi tiêu.")
        st.error("**Khách hàng ít hoạt động:** Win-back campaign — Gửi Email nhắc nhở, tặng discount kích hoạt.")