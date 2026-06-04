import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from itertools import combinations
import os, time

st.set_page_config(
    page_title="Olist · Data Mining Demo",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0f1117; color: #e8e8e8; }

/* ── Hero ── */
.hero {
    text-align: center; padding: 5rem 2rem 3rem 2rem;
}
.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 3.8rem; color: #fff;
    line-height: 1.15; margin-bottom: 1rem;
}
.hero-sub {
    font-size: 1.1rem; color: #888; max-width: 600px;
    margin: 0 auto 2.5rem auto; line-height: 1.7;
}
.badge {
    display: inline-block; background: #1a1d27;
    border: 1px solid #2a2d3a; border-radius: 20px;
    padding: 0.3rem 1rem; margin: 0.2rem;
    font-size: 0.82rem; color: #aaa;
}

/* ── Step header ── */
.step-header {
    background: #1a1d27; border: 1px solid #2a2d3a;
    border-radius: 16px; padding: 1.5rem 2rem;
    margin: 2rem 0 1.5rem 0; position: relative; overflow: hidden;
    text-align: center;
}
.step-header::before {
    content: ''; position: absolute;
    left: 0; top: 0; bottom: 0; width: 4px;
}
.step-header.eda::before    { background: #4e8ef7; }
.step-header.prep::before   { background: #f79c4e; }
.step-header.wh::before     { background: #a569f7; }
.step-header.cube::before   { background: #00c4cc; }
.step-header.cluster::before{ background: #00c07f; }

.step-num {
    font-size: 0.75rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 2px; color: #555;
    margin-bottom: 0.3rem;
}
.step-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.8rem; color: #fff; margin: 0;
}
.step-desc { color: #888; margin-top: 0.3rem; font-size: 0.95rem; }

/* ── KPI card ── */
.kpi-card {
    background: #1a1d27; border: 1px solid #2a2d3a;
    border-radius: 14px; padding: 1.2rem 1.4rem;
    position: relative; overflow: hidden;
}
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:14px 14px 0 0; }
.kpi-card.green::before  { background: #00c07f; }
.kpi-card.blue::before   { background: #4e8ef7; }
.kpi-card.orange::before { background: #f79c4e; }
.kpi-card.purple::before { background: #a569f7; }
.kpi-card.cyan::before   { background: #00c4cc; }
.kpi-label { font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:#555; margin-bottom:0.4rem; }
.kpi-value { font-family:'DM Serif Display',serif; font-size:1.8rem; color:#fff; line-height:1; }
.kpi-sub   { font-size:0.78rem; color:#555; margin-top:0.3rem; }

/* ── Info box ── */
.info-box {
    background: #1a1d27; border: 1px solid #2a2d3a;
    border-left: 4px solid #4e8ef7;
    border-radius: 10px; padding: 1rem 1.2rem;
    margin: 0.8rem 0; font-size: 0.88rem; color: #bbb; line-height: 1.8;
}
.info-box.orange { border-left-color: #f79c4e; }
.info-box.purple { border-left-color: #a569f7; }
.info-box.cyan   { border-left-color: #00c4cc; }
.info-box.green  { border-left-color: #00c07f; }

/* ── Pipeline visual ── */
.pipeline {
    display: flex; align-items: center; justify-content: center;
    gap: 0.5rem; flex-wrap: wrap;
    padding: 1.5rem; background: #1a1d27;
    border-radius: 14px; border: 1px solid #2a2d3a;
    margin-bottom: 2rem;
}
.pipe-step {
    background: #0f1117; border: 1px solid #2a2d3a;
    border-radius: 10px; padding: 0.6rem 1.1rem;
    font-size: 0.85rem; color: #ccc; white-space: nowrap;
}
.pipe-step.active { border-color: #4e8ef7; color: #4e8ef7; font-weight: 600; }
.pipe-arrow { color: #333; font-size: 1.2rem; }

/* ── Section divider ── */
.divider { border: none; border-top: 1px solid #1e2130; margin: 3rem 0; }
</style>
""", unsafe_allow_html=True)

# Session state 
if "started" not in st.session_state:
    st.session_state.started = False
if "step" not in st.session_state:
    st.session_state.step = 0   # 0=hero, 1=EDA, 2=Prep, 3=WH, 4=Cube, 5=Cluster

# Load data 
@st.cache_data
def load_data():
    sales     = pd.read_csv("data/processed/final_sales.csv")
    fact      = pd.read_csv("data/warehouse/fact_sales.csv")
    dim_prod  = pd.read_csv("data/warehouse/dim_product.csv")
    dim_date  = pd.read_csv("data/warehouse/dim_date.csv")
    clusters  = pd.read_csv("outputs/customer_clusters.csv")

    sales["order_purchase_timestamp"] = pd.to_datetime(sales["order_purchase_timestamp"])
    sales["order_month"]  = sales["order_month"].astype(str)
    sales["category_clean"] = sales["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    sales["payment_type"]   = sales["payment_type"].fillna("unknown")

    fact = fact.merge(dim_prod, on="product_id", how="left")
    fact["category_clean"] = fact["product_category_name"].fillna("unknown").str.replace("_"," ").str.title()
    state_map = sales[["customer_id","customer_state"]].drop_duplicates("customer_id")
    fact = fact.merge(state_map, on="customer_id", how="left")
    fact["customer_state"] = fact["customer_state"].fillna("unknown")
    fact["payment_type"]   = fact["payment_type"].fillna("unknown")

    return sales, fact, dim_date, clusters

@st.cache_data
def load_cube():
    path = "outputs/iceberg_cube.csv"
    if not (os.path.exists(path) and os.path.getsize(path) > 0):
        return pd.DataFrame(), False
    raw = pd.read_csv(path)
    DIM_COLS = {
        "order_month":           "Month",
        "customer_state":        "State",
        "product_category_name": "Category",
        "payment_type":          "Payment",
    }
    def cuboid_name(row):
        active = [lbl for col, lbl in DIM_COLS.items() if str(row[col]).upper() != "ALL"]
        return "ALL*" if not active else " × ".join(active)
    def cell_label(row):
        parts = [str(row[col]) for col in DIM_COLS if str(row[col]).upper() != "ALL"]
        return " | ".join(parts) if parts else "ALL*"

    raw["cuboid"]        = raw.apply(cuboid_name, axis=1)
    raw["label"]         = raw.apply(cell_label, axis=1)
    raw["total_revenue"] = raw["total_sales"]
    raw["avg_review"]    = raw["avg_review_score"]
    return raw, True

try:
    df, fact, dim_date, clusters = load_data()
    cube_df, cube_loaded = load_cube()
except FileNotFoundError as e:
    st.error(f"⚠️ Không tìm thấy file: {e}")
    st.stop()

# Pre-compute orders (groupby order_id — không double-count)
orders = df.groupby("order_id").agg(
    total_amount            = ("total_amount",              "first"),
    customer_unique_id      = ("customer_unique_id",        "first"),
    customer_state          = ("customer_state",            "first"),
    order_month             = ("order_month",               "first"),
    order_purchase_timestamp= ("order_purchase_timestamp",  "first"),
    payment_type            = ("payment_type",              "first"),
).reset_index()

TOTAL_REVENUE   = orders["total_amount"].sum()
TOTAL_ORDERS    = len(orders)
TOTAL_CUSTOMERS = orders["customer_unique_id"].nunique()
AOV             = TOTAL_REVENUE / TOTAL_ORDERS

CLUSTER_COLORS = {
    "Khách hàng tiềm năng":    "#4e8ef7",
    "Khách hàng giá trị thấp": "#f79c4e",
    "Khách hàng giá trị cao":  "#00c07f",
    "Khách hàng ít hoạt động": "#a569f7",
}

# Helpers
def kpi(col, color, label, value, sub=""):
    col.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

def step_header(cls, num, title, desc):
    st.markdown(f"""
    <div class="step-header {cls}">
        <div class="step-title">{title}</div>
        <div class="step-desc">{desc}</div>
    </div>""", unsafe_allow_html=True)

def pipeline_bar(active_idx):
    steps = [" EDA", " Tiền xử lý", " Data Warehouse", " Iceberg Cube", " Clustering"]
    parts = []
    for i, s in enumerate(steps):
        cls = "pipe-step active" if i == active_idx else "pipe-step"
        parts.append(f'<div class="{cls}">{s}</div>')
        if i < len(steps)-1:
            parts.append('<div class="pipe-arrow">→</div>')
    st.markdown(f'<div class="pipeline">{"".join(parts)}</div>', unsafe_allow_html=True)

def nav_buttons(step_idx, total=5):
    cols = st.columns([1,4,1])
    with cols[0]:
        if step_idx > 1:
            if st.button("← Return", use_container_width=True):
                st.session_state.step = step_idx - 1
                st.rerun()
    with cols[2]:
        if step_idx < total:
            label = "Next →"
            if st.button(label, use_container_width=True, type="primary"):
                st.session_state.step = step_idx + 1
                st.rerun()
        else:
            if st.button("Review again", use_container_width=True):
                st.session_state.step = 1
                st.rerun()

# HERO PAGE
if not st.session_state.started:
    st.markdown("""
    <div class="hero">
        <div class="hero-title"> Olist E-Commerce<br>Analytics System</div>
        <div class="hero-sub">
            Khám phá toàn bộ pipeline Data Mining — từ dữ liệu thô đến insight
            kinh doanh — qua từng bước EDA, tiền xử lý, Data Warehouse,
            Iceberg Cube (BUC Top-Down) và Clustering.
        </div>
        <span class="badge"> 118,310 records</span>
        <span class="badge"> Brazilian E-Commerce</span>
        <span class="badge"> 2016–2018</span>
        <span class="badge"> Olist Dataset</span>
    </div>
    """, unsafe_allow_html=True)

    # KPI snapshot
    c1,c2,c3,c4 = st.columns(4)
    kpi(c1,"green","Tổng Doanh Thu",  f"R$ {TOTAL_REVENUE/1e6:.2f}M","toàn bộ dataset")
    kpi(c2,"blue", "Số Đơn Hàng",     f"{TOTAL_ORDERS:,}",           "đơn duy nhất")
    kpi(c3,"orange","Số Khách Hàng",  f"{TOTAL_CUSTOMERS:,}",        "unique customers")
    kpi(c4,"purple","AOV",            f"R$ {AOV:.2f}",               "giá trị đơn TB")

    st.markdown("<br>", unsafe_allow_html=True)

    # Pipeline overview
    st.markdown("""
    <div class="pipeline">
        <div class="pipe-step"> Raw Data</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step active"> EDA</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step active"> Tiền xử lý</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step active"> Data Warehouse</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step active"> Iceberg Cube</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step active"> Clustering</div>
        <div class="pipe-arrow">→</div>
        <div class="pipe-step"> Insight</div>
    </div>
    """, unsafe_allow_html=True)

    col_btn = st.columns([2,2,2])[1]
    with col_btn:
        if st.button(" Start demo", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.session_state.step = 1
            st.rerun()
    st.stop()

# STEP 1 — EDA
if st.session_state.step == 1:
    pipeline_bar(0)
    step_header("eda", 1, " Exploratory Data Analysis",
                "Khám phá tổng quan dataset Olist — phân phối, xu hướng, các chiều dữ liệu chính.")

    st.markdown("""
    <div class="info-box">
        <b>Dataset:</b> Olist Brazilian E-Commerce · 9 bảng gốc từ Kaggle<br>
        <b>Thời gian:</b> 09/2016 – 09/2018 &nbsp;·&nbsp; <b>Đơn hàng:</b> 98,666 &nbsp;·&nbsp;
        <b>Khách hàng:</b> 95,420 &nbsp;·&nbsp; <b>Sellers:</b> 3,095 &nbsp;·&nbsp; <b>Products:</b> 32,216
    </div>
    """, unsafe_allow_html=True)

    # Doanh thu theo tháng
    st.markdown("####  Doanh Thu Theo Tháng")
    monthly = (orders.groupby("order_month")["total_amount"].sum()
               .reset_index().rename(columns={"order_month":"Tháng","total_amount":"Doanh Thu (R$)"})
               .sort_values("Tháng"))
    monthly = monthly[monthly["Tháng"].between("2017-01","2018-08")]
    fig_m = px.area(monthly, x="Tháng", y="Doanh Thu (R$)",
                    color_discrete_sequence=["#4e8ef7"], template="plotly_dark")
    fig_m.update_traces(fill="tozeroy", fillcolor="rgba(78,142,247,0.12)", line=dict(width=2.5))
    fig_m.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                        margin=dict(l=0,r=0,t=10,b=0),
                        xaxis=dict(showgrid=False, tickangle=-30),
                        yaxis=dict(gridcolor="#1f2230"), height=260)
    st.plotly_chart(fig_m, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # Top category
        st.markdown("#### Top 10 Category")
        cat = (df.drop_duplicates(["order_id","product_category_name"])
               .groupby("category_clean")["order_id"].count()
               .nlargest(10).reset_index()
               .rename(columns={"category_clean":"Category","order_id":"Đơn"})
               .sort_values("Đơn"))
        fig_c = px.bar(cat, x="Đơn", y="Category", orientation="h",
                       color="Đơn", color_continuous_scale=["#1a3a5c","#4e8ef7"],
                       template="plotly_dark")
        fig_c.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                            margin=dict(l=0,r=0,t=5,b=0), coloraxis_showscale=False,
                            yaxis=dict(showgrid=False), xaxis=dict(gridcolor="#1f2230"), height=320)
        st.plotly_chart(fig_c, use_container_width=True)

    with col2:
        # Review score distribution
        st.markdown("####  Phân Phối Review Score")
        rev = df["review_score"].dropna().value_counts().sort_index().reset_index()
        rev.columns = ["Score","Số đơn"]
        rev["Score"] = rev["Score"].astype(str)
        fig_r = px.bar(rev, x="Score", y="Số đơn",
                       color="Số đơn", color_continuous_scale=["#2a1a3a","#a569f7"],
                       template="plotly_dark")
        fig_r.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                            margin=dict(l=0,r=0,t=5,b=0), coloraxis_showscale=False,
                            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"), height=320)
        st.plotly_chart(fig_r, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        # Payment type
        st.markdown("####  Phương Thức Thanh Toán")
        pay = (orders.groupby("payment_type")["order_id"].count()
               .reset_index().rename(columns={"payment_type":"Loại","order_id":"Đơn"})
               .sort_values("Đơn", ascending=False))
        fig_p = px.pie(pay, values="Đơn", names="Loại",
                       color_discrete_sequence=["#4e8ef7","#f79c4e","#a569f7","#00c07f"],
                       template="plotly_dark", hole=0.4)
        fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=5,b=0), height=300)
        st.plotly_chart(fig_p, use_container_width=True)

    with col4:
        # Top state
        st.markdown("#### Top 8 Bang Theo Đơn Hàng")
        st_df = (orders.groupby("customer_state")["order_id"].count()
                 .reset_index().rename(columns={"customer_state":"Bang","order_id":"Đơn"})
                 .sort_values("Đơn", ascending=False).head(8))
        fig_s = px.bar(st_df, x="Bang", y="Đơn",
                       color="Đơn", color_continuous_scale=["#1a3a5c","#00c4cc"],
                       template="plotly_dark")
        fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                            margin=dict(l=0,r=0,t=5,b=0), coloraxis_showscale=False,
                            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"), height=300)
        st.plotly_chart(fig_s, use_container_width=True)

    # Key findings
    st.markdown("""
    <div class="info-box">
        <b> Key Findings từ EDA:</b><br>
        • Doanh thu tăng mạnh từ Q3/2017, đỉnh điểm tháng 11/2017 (Black Friday)<br>
        • <b>Cama Mesa Banho</b> và <b>Beleza Saúde</b> là 2 category bán chạy nhất<br>
        • <b>87%</b> đơn hàng thanh toán qua thẻ tín dụng<br>
        • <b>SP (São Paulo)</b> chiếm ~50% tổng đơn hàng — thị trường trọng tâm<br>
        • Review score trung bình <b>4.04/5</b> — khách hàng khá hài lòng
    </div>
    """, unsafe_allow_html=True)
    nav_buttons(1)

# STEP 2 — TIỀN XỬ LÝ
elif st.session_state.step == 2:
    pipeline_bar(1)
    step_header("prep", 2, " Tiền Xử Lý Dữ Liệu",
                "Gộp 9 bảng gốc → 1 bảng tổng hợp, xử lý missing, tạo biến phái sinh.")

    st.markdown("""
    <div class="info-box orange">
        <b>Input:</b> 9 bảng CSV gốc từ Kaggle (orders, items, customers, products, sellers, payments, reviews, geolocation, category_translation)<br>
        <b>Output:</b> <code>final_sales.csv</code> — 118,310 dòng · 14 cột · sẵn sàng cho phân tích
    </div>
    """, unsafe_allow_html=True)

    # Quy trình
    st.markdown("####  Quy Trình Tiền Xử Lý")
    steps_prep = [
        ("1. Merge bảng", "Join orders ← items ← customers ← products ← payments ← reviews theo order_id và foreign keys"),
        ("2. Xử lý missing", "product_category_name: fillna('unknown') · review_score: giữ NaN (không impute để tránh bias) · payment_type: fillna('unknown')"),
        ("3. Loại duplicate", "drop_duplicates('order_id') cho các phân tích cấp đơn hàng — giữ nguyên cấp item cho Warehouse"),
        ("4. Tạo biến mới", "total_amount = price + freight_value · order_month = YYYY-MM · delivery_days = delivered_date - purchase_date"),
        ("5. Lọc thời gian", "Giữ 2016-09 đến 2018-08, loại tháng đầu/cuối có dữ liệu thưa"),
    ]
    for title, desc in steps_prep:
        st.markdown(f"""
        <div class="info-box orange" style="margin:0.4rem 0;">
            <b>{title}</b><br><span style="color:#999">{desc}</span>
        </div>""", unsafe_allow_html=True)

    # Thống kê mô tả
    st.markdown("####  Thống Kê Mô Tả Sau Tiền Xử Lý")
    num_cols = ["price","freight_value","total_amount","review_score","delivery_days"]
    desc = df[num_cols].describe().round(2)
    desc.index = ["Count","Mean","Std","Min","25%","Median","75%","Max"]
    desc.columns = ["Giá SP (R$)","Phí Ship (R$)","Tổng TT (R$)","Review Score","Giao hàng (ngày)"]
    st.dataframe(desc.style.format("{:,.2f}").background_gradient(cmap="Blues", axis=1),
                 use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    kpi(c1,"orange","Tổng dòng",   f"{len(df):,}",        "sau merge")
    kpi(c2,"orange","Số cột",      "14",                  "feature cuối")
    kpi(c3,"orange","Missing (%)", f"{df.isnull().sum().sum()/df.size*100:.2f}%", "toàn bảng")
    kpi(c4,"orange","Thời gian",   "2016–2018",           "23 tháng")

    with st.expander(" Chi tiết missing values"):
        miss = df.isnull().sum().reset_index()
        miss.columns = ["Cột","Thiếu"]
        miss["Tỉ lệ (%)"] = (miss["Thiếu"]/len(df)*100).round(2)
        st.dataframe(miss[miss["Thiếu"]>0], use_container_width=True, hide_index=True)

    with st.expander(" Xem 10 dòng đầu final_sales.csv"):
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    nav_buttons(2)

# STEP 3 — DATA WAREHOUSE
elif st.session_state.step == 3:
    pipeline_bar(2)
    step_header("wh", 3, " Data Warehouse",
                "Thiết kế Star Schema — 1 Fact table + 5 Dimension tables.")

    st.markdown("""
    <div class="info-box purple">
        <b>Mô hình:</b> Star Schema &nbsp;·&nbsp;
        <b>Grain:</b> 1 dòng = 1 order item &nbsp;·&nbsp;
        <b>Fact table:</b> fact_sales &nbsp;·&nbsp;
        <b>Dim tables:</b> dim_date · dim_customer · dim_product · dim_seller · dim_payment
    </div>
    """, unsafe_allow_html=True)

    # Star Schema diagram (SVG)
    st.markdown("####  Star Schema")
    st.markdown("""
    <div style="background:#1a1d27; border:1px solid #2a2d3a; border-radius:14px; padding:1.5rem; text-align:center;">
    <svg viewBox="0 0 600 400" xmlns="http://www.w3.org/2000/svg" style="max-width:100%;height:340px;">
      <!-- Fact center -->
      <rect x="210" y="155" width="180" height="90" rx="10" fill="#1e2a3a" stroke="#4e8ef7" stroke-width="2"/>
      <text x="300" y="192" text-anchor="middle" fill="#4e8ef7" font-size="13" font-weight="bold" font-family="DM Sans">fact_sales</text>
      <text x="300" y="210" text-anchor="middle" fill="#888" font-size="10" font-family="DM Sans">order_id · product_id</text>
      <text x="300" y="226" text-anchor="middle" fill="#888" font-size="10" font-family="DM Sans">price · freight · total_amount</text>
      <!-- dim_date top -->
      <rect x="220" y="20" width="160" height="60" rx="8" fill="#1a1d27" stroke="#a569f7" stroke-width="1.5"/>
      <text x="300" y="47" text-anchor="middle" fill="#a569f7" font-size="12" font-weight="bold" font-family="DM Sans">dim_date</text>
      <text x="300" y="63" text-anchor="middle" fill="#666" font-size="10" font-family="DM Sans">order_month · year · quarter</text>
      <line x1="300" y1="80" x2="300" y2="155" stroke="#2a2d3a" stroke-width="1.5" stroke-dasharray="4"/>
      <!-- dim_customer left -->
      <rect x="20" y="155" width="160" height="60" rx="8" fill="#1a1d27" stroke="#a569f7" stroke-width="1.5"/>
      <text x="100" y="182" text-anchor="middle" fill="#a569f7" font-size="12" font-weight="bold" font-family="DM Sans">dim_customer</text>
      <text x="100" y="198" text-anchor="middle" fill="#666" font-size="10" font-family="DM Sans">customer_id · state</text>
      <line x1="180" y1="185" x2="210" y2="200" stroke="#2a2d3a" stroke-width="1.5" stroke-dasharray="4"/>
      <!-- dim_product right -->
      <rect x="420" y="155" width="160" height="60" rx="8" fill="#1a1d27" stroke="#a569f7" stroke-width="1.5"/>
      <text x="500" y="182" text-anchor="middle" fill="#a569f7" font-size="12" font-weight="bold" font-family="DM Sans">dim_product</text>
      <text x="500" y="198" text-anchor="middle" fill="#666" font-size="10" font-family="DM Sans">product_id · category</text>
      <line x1="390" y1="200" x2="420" y2="185" stroke="#2a2d3a" stroke-width="1.5" stroke-dasharray="4"/>
      <!-- dim_payment bottom-left -->
      <rect x="80" y="310" width="160" height="60" rx="8" fill="#1a1d27" stroke="#a569f7" stroke-width="1.5"/>
      <text x="160" y="337" text-anchor="middle" fill="#a569f7" font-size="12" font-weight="bold" font-family="DM Sans">dim_payment</text>
      <text x="160" y="353" text-anchor="middle" fill="#666" font-size="10" font-family="DM Sans">payment_type</text>
      <line x1="210" y1="232" x2="200" y2="310" stroke="#2a2d3a" stroke-width="1.5" stroke-dasharray="4"/>
      <!-- dim_seller bottom-right -->
      <rect x="360" y="310" width="160" height="60" rx="8" fill="#1a1d27" stroke="#a569f7" stroke-width="1.5"/>
      <text x="440" y="337" text-anchor="middle" fill="#a569f7" font-size="12" font-weight="bold" font-family="DM Sans">dim_seller</text>
      <text x="440" y="353" text-anchor="middle" fill="#666" font-size="10" font-family="DM Sans">seller_id · state</text>
      <line x1="390" y1="232" x2="400" y2="310" stroke="#2a2d3a" stroke-width="1.5" stroke-dasharray="4"/>
    </svg>
    </div>
    """, unsafe_allow_html=True)

    # Stats warehouse
    st.markdown("####  Thống Kê Warehouse")
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1,"purple","fact_sales",   f"{len(fact):,} dòng",    "110,197 order items")
    kpi(c2,"purple","dim_product",  "32,216 sản phẩm",        "2 cột")
    kpi(c3,"purple","dim_date",     "23 tháng",               "4 cột")
    kpi(c4,"purple","dim_payment",  "5 loại",                 "1 cột")
    kpi(c5,"purple","dim_customer", "98,666 customers",       "3 cột")

    with st.expander(" Xem fact_sales (10 dòng đầu)"):
        st.dataframe(fact.head(10), use_container_width=True, hide_index=True)
    with st.expander(" Xem dim_date"):
        st.dataframe(dim_date, use_container_width=True, hide_index=True)

    nav_buttons(3)

# STEP 4 — ICEBERG CUBE
elif st.session_state.step == 4:
    pipeline_bar(3)
    step_header("cube", 4, " Iceberg Cube — BUC Top-Down",
                "Khai phá data cube đa chiều, cắt tỉa theo min_support để giữ lại các cell có ý nghĩa.")

    MIN_SUP = cube_df["support_count"].min() if cube_loaded else 200
    TOTAL_CELLS = len(cube_df) if cube_loaded else 0

    st.markdown(f"""
    <div class="info-box cyan">
        <b>Thuật toán:</b> BUC (Bottom-Up Computation) theo hướng Top-Down<br>
        <b>Dimensions:</b> Month · State · Category · Payment &nbsp;(4 chiều)<br>
        <b>Measures:</b> order_count · total_sales · avg_review_score · avg_delivery_days<br>
        <b>Min support:</b> {MIN_SUP:,} records &nbsp;·&nbsp; <b>Cells giữ lại:</b> {TOTAL_CELLS:,} / nhiều nghìn cells lý thuyết
    </div>
    """, unsafe_allow_html=True)

    # Cơ chế BUC
    st.markdown("#### Cơ Chế BUC Top-Down")
    buc_steps = [
        ("1. Bắt đầu từ ALL*", f"Apex cuboid — tổng toàn bộ {TOTAL_ORDERS:,} đơn, không phân chia dimension nào"),
        ("2. Duyệt xuống 1-dim cuboids", "Tính riêng từng dimension: cuboid(Month), cuboid(State), cuboid(Category), cuboid(Payment)"),
        ("3. Pruning", f"Cell nào có support_count < min_support → cắt tỉa, không mở rộng xuống nhánh con → tiết kiệm bộ nhớ và thời gian"),
        ("4. Tiếp tục 2-dim, 3-dim, 4-dim", "Chỉ tính các tổ hợp từ những cell không bị pruned ở bước trên"),
        ("5. Iceberg condition", "Kết quả cuối chỉ chứa cells thỏa support ≥ ngưỡng → đây là Iceberg Cube"),
    ]
    for t, d in buc_steps:
        st.markdown(f"""
        <div class="info-box cyan" style="margin:0.3rem 0;">
            <b>{t}</b><br><span style="color:#999">{d}</span>
        </div>""", unsafe_allow_html=True)

    if not cube_loaded:
        st.warning(" `outputs/iceberg_cube.csv` chưa có — không thể hiển thị kết quả thực.")
    else:
        # Lattice Sankey
        st.markdown("####  Lattice Cuboid — Cây Duyệt BUC")
        DIMS_LIST = ["Month","State","Category","Payment"]
        lattice_nodes = ["ALL*"] + [
            " × ".join(c)
            for r in range(1, len(DIMS_LIST)+1)
            for c in combinations(DIMS_LIST, r)
        ]
        cell_counts = cube_df.groupby("cuboid").size().to_dict()
        node_labels, node_colors = [], []
        for n in lattice_nodes:
            cnt = cell_counts.get(n, 0)
            node_labels.append(f"{n}<br>({cnt} cells)" if cnt else f"{n}<br>(pruned ✗)")
            node_colors.append("#00c4cc" if n=="ALL*" else ("#00c07f" if cnt>0 else "#2a2a3a"))

        src, tgt, vals = [], [], []
        for i, n in enumerate(lattice_nodes):
            n_set = set(n.replace("ALL*","").replace(" × ","||").split("||")) - {""}
            for j, m in enumerate(lattice_nodes):
                if i==j: continue
                m_set = set(m.replace("ALL*","").replace(" × ","||").split("||")) - {""}
                if len(m_set)==len(n_set)+1 and n_set.issubset(m_set):
                    src.append(i); tgt.append(j)
                    vals.append(max(cell_counts.get(m,1),1))

        col_l, col_r = st.columns([3,2])
        with col_l:
            fig_lat = go.Figure(go.Sankey(
                node=dict(label=node_labels, color=node_colors, pad=12, thickness=16,
                          line=dict(color="#0f1117", width=0.5)),
                link=dict(source=src, target=tgt, value=vals,
                          color="rgba(0,196,204,0.1)")
            ))
            fig_lat.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#ccc",family="DM Sans",size=10),
                                  height=380, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_lat, use_container_width=True)

        with col_r:
            st.markdown("**Số cell theo cuboid level**")
            lvl_cnt = cube_df.groupby("cuboid_level").size().reset_index()
            lvl_cnt.columns = ["Level","Số cell"]
            lvl_cnt["Mô tả"] = lvl_cnt["Level"].map({
                0:"ALL* (apex)", 1:"1-dim cuboids",
                2:"2-dim cuboids", 3:"3-dim cuboids", 4:"4-dim cuboids"
            })
            st.dataframe(lvl_cnt[["Level","Mô tả","Số cell"]],
                         use_container_width=True, hide_index=True)
            total_cells_nd = len(cube_df[cube_df["cuboid_level"]>0])
            st.metric("Tổng cells (không ALL*)", f"{total_cells_nd:,}")
            st.metric("Min support dùng", f"{int(cube_df['support_count'].min()):,}")

        # Top 10 nổi bật
        st.markdown("####  Top 10 Cell Nổi Bật (order_count cao nhất)")
        top10 = (cube_df[cube_df["cuboid_level"]>0]
                 .nlargest(10,"order_count")
                 [["cuboid","label","order_count","total_revenue","avg_review","avg_delivery_days"]]
                 .copy())
        top10["total_revenue"]    = top10["total_revenue"].map("R$ {:,.0f}".format)
        top10["avg_review"]       = top10["avg_review"].map("{:.2f}".format)
        top10["avg_delivery_days"]= top10["avg_delivery_days"].map("{:.1f} ngày".format)
        top10["order_count"]      = top10["order_count"].map("{:,}".format)
        top10.columns = ["Cuboid","Cell","Số đơn","Doanh thu","Review TB","Giao hàng TB"]
        st.dataframe(top10, use_container_width=True, hide_index=True)

        # Heatmap Category × State
        st.markdown("####  Heatmap Category × State")
        h_data = cube_df[
            (cube_df["cuboid"]=="Category × State") |
            (cube_df["cuboid"]=="State × Category")
        ].copy()
        if h_data.empty:
            # fallback từ fact
            h_data = (fact.drop_duplicates("order_id")
                      .groupby(["category_clean","customer_state"])
                      .agg(order_count=("order_id","count")).reset_index())
            h_data = h_data[h_data["order_count"] >= int(cube_df["support_count"].min())]
            h_data = h_data.rename(columns={"category_clean":"product_category_name",
                                            "customer_state":"customer_state"})
        else:
            h_data = (fact.drop_duplicates("order_id")
                      .groupby(["category_clean","customer_state"])
                      .agg(order_count=("order_id","count")).reset_index())
            h_data = h_data[h_data["order_count"] >= int(cube_df["support_count"].min())]

        top_cat   = h_data.groupby("category_clean")["order_count"].sum().nlargest(10).index
        top_state = h_data.groupby("customer_state")["order_count"].sum().nlargest(10).index
        heat = h_data[h_data["category_clean"].isin(top_cat) &
                      h_data["customer_state"].isin(top_state)]
        pivot = heat.pivot_table(index="category_clean", columns="customer_state",
                                 values="order_count", fill_value=0)
        fig_h = px.imshow(pivot, color_continuous_scale="Blues",
                          template="plotly_dark", aspect="auto",
                          labels={"color":"Số đơn","x":"Bang","y":"Category"})
        fig_h.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                            margin=dict(l=0,r=0,t=10,b=0), height=380)
        st.plotly_chart(fig_h, use_container_width=True)
        st.caption("Chỉ hiển thị top 10 category × top 10 bang — cells dưới min_support đã bị pruned")

    nav_buttons(4)

# STEP 5 — CLUSTERING
elif st.session_state.step == 5:
    pipeline_bar(4)
    step_header("cluster", 5, " Customer Clustering — RFM & K-Means",
                "Phân cụm khách hàng theo hành vi mua sắm để cá nhân hóa chiến lược kinh doanh.")

    st.markdown("""
    <div class="info-box green">
        <b>Phương pháp:</b> RFM (Recency · Frequency · Monetary) + StandardScaler + PCA + K-Means (k=4)<br>
        <b>Chọn k:</b> Elbow Method + Silhouette Score &nbsp;·&nbsp;
        <b>Kết quả:</b> 4 clusters · 95,420 khách hàng được phân loại
    </div>
    """, unsafe_allow_html=True)

    # Quy trình
    st.markdown("####  Quy Trình Clustering")
    rfm_steps = [
        ("1. Tính RFM", "Recency = ngày từ đơn cuối đến snapshot · Frequency = số đơn · Monetary = tổng chi tiêu"),
        ("2. StandardScaler", "Chuẩn hóa 3 chiều RFM về mean=0, std=1 để K-Means không bị lệch theo đơn vị"),
        ("3. PCA 2D", "Giảm chiều từ 3D xuống 2D để visualize phân bố cluster"),
        ("4. K-Means k=4", "Chọn k=4 theo Elbow + Silhouette · Random state=42 · n_init=10"),
        ("5. Gán nhãn", "Phân tích profile từng cluster → đặt tên có ý nghĩa kinh doanh"),
    ]
    for t, d in rfm_steps:
        st.markdown(f"""
        <div class="info-box green" style="margin:0.3rem 0;">
            <b>{t}</b><br><span style="color:#999">{d}</span>
        </div>""", unsafe_allow_html=True)

    # Scatter PCA
    st.markdown("####  Phân Bổ Cluster — PCA 2D")
    sample = clusters.sample(min(5000, len(clusters)), random_state=42)
    fig_sc = px.scatter(
        sample, x="pca_1", y="pca_2",
        color="cluster_name", color_discrete_map=CLUSTER_COLORS,
        template="plotly_dark", opacity=0.55,
        labels={"pca_1":"PCA 1","pca_2":"PCA 2","cluster_name":"Cluster"},
        hover_data={"recency":True,"frequency":True,"monetary":":.0f",
                    "pca_1":False,"pca_2":False},
    )
    fig_sc.update_traces(marker=dict(size=4))
    fig_sc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
        margin=dict(l=0,r=0,t=10,b=0), height=420,
        xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
        legend=dict(bgcolor="rgba(26,29,39,0.9)", bordercolor="#2a2d3a", title="Cluster"),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    # Profile table
    st.markdown("####  Profile Từng Cluster")
    profile = clusters.groupby("cluster_name").agg(
        Số_khách    = ("customer_unique_id","count"),
        Recency_TB  = ("recency",           "mean"),
        Frequency_TB= ("frequency",         "mean"),
        Monetary_TB = ("monetary",          "mean"),
        AOV_TB      = ("avg_order_value",   "mean"),
        Review_TB   = ("avg_review_score",  "mean"),
        Delivery_TB = ("avg_delivery_days", "mean"),
    ).round(1).reset_index()
    profile["Tỉ lệ (%)"] = (profile["Số_khách"]/profile["Số_khách"].sum()*100).round(1)
    profile = profile.rename(columns={
        "cluster_name":"Cluster","Số_khách":"Số khách",
        "Recency_TB":"Recency TB","Frequency_TB":"Frequency TB",
        "Monetary_TB":"Monetary TB (R$)","AOV_TB":"AOV TB (R$)",
        "Review_TB":"Review TB","Delivery_TB":"Giao hàng TB"
    })
    st.dataframe(
        profile.style.format({
            "Recency TB":"{:.1f}","Frequency TB":"{:.1f}",
            "Monetary TB (R$)":"R$ {:,.1f}","AOV TB (R$)":"R$ {:,.1f}",
            "Review TB":"{:.2f}","Giao hàng TB":"{:.1f}","Tỉ lệ (%)":"{:.1f}%"
        }).background_gradient(subset=["Monetary TB (R$)"], cmap="Greens"),
        use_container_width=True, hide_index=True
    )

    # Bar + Radar
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        fig_bc = px.bar(profile, x="Cluster", y="Số khách",
                        color="Cluster", color_discrete_map=CLUSTER_COLORS,
                        text="Tỉ lệ (%)", template="plotly_dark",
                        title="Phân bổ số khách theo cluster")
        fig_bc.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_bc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                             margin=dict(l=0,r=0,t=40,b=0), height=320, showlegend=False,
                             xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"))
        st.plotly_chart(fig_bc, use_container_width=True)

    with col_b2:
        fig_bm = px.bar(profile, x="Cluster", y="Monetary TB (R$)",
                        color="Cluster", color_discrete_map=CLUSTER_COLORS,
                        template="plotly_dark", title="Monetary TB theo cluster")
        fig_bm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                             margin=dict(l=0,r=0,t=40,b=0), height=320, showlegend=False,
                             xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"))
        st.plotly_chart(fig_bm, use_container_width=True)

    # Radar
    st.markdown("####  Radar Chart — So Sánh Đặc Trưng")
    radar_metrics = ["Recency TB","Frequency TB","Monetary TB (R$)","Review TB","Giao hàng TB"]
    radar_df = profile[["Cluster"]+radar_metrics].copy()
    for col in radar_metrics:
        mn, mx = radar_df[col].min(), radar_df[col].max()
        radar_df[col] = (radar_df[col]-mn)/(mx-mn+1e-9)

    fig_radar = go.Figure()
    for _, row in radar_df.iterrows():
        vals = [row[m] for m in radar_metrics] + [row[radar_metrics[0]]]
        cats = radar_metrics + [radar_metrics[0]]
        color = CLUSTER_COLORS.get(row["Cluster"], "#fff")
        r,g,b = int(color[1:3],16), int(color[3:5],16), int(color[5:7],16)
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=cats, fill="toself", name=row["Cluster"],
            line_color=color, fillcolor=f"rgba({r},{g},{b},0.12)", opacity=0.9,
        ))
    fig_radar.update_layout(
        polar=dict(bgcolor="rgba(26,29,39,1)",
                   radialaxis=dict(visible=True, range=[0,1], gridcolor="#2a2d3a",
                                   tickfont=dict(color="#555")),
                   angularaxis=dict(gridcolor="#2a2d3a", tickfont=dict(color="#ccc"))),
        paper_bgcolor="rgba(0,0,0,0)", template="plotly_dark",
        legend=dict(bgcolor="rgba(26,29,39,0.9)", bordercolor="#2a2d3a"),
        height=420, margin=dict(l=40,r=40,t=20,b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.caption("Các chỉ số đã chuẩn hóa [0,1] — Radar cho thấy rõ đặc trưng phân biệt từng cluster")

    # Business recommendations
    st.markdown("####  Gợi Ý Chiến Lược Theo Cluster")
    recs = {
        "Khách hàng giá trị cao":    ("🟢","Ưu tiên giữ chân — loyalty program, early access, ưu đãi VIP"),
        "Khách hàng tiềm năng":      ("🔵","Nurture — gợi ý sản phẩm phù hợp, khuyến khích mua lần 2"),
        "Khách hàng ít hoạt động":   ("🟣","Win-back campaign — email nhắc nhở, discount kích hoạt lại"),
        "Khách hàng giá trị thấp":   ("🟠","Upsell — bundle offers, free shipping khi đạt ngưỡng chi tiêu"),
    }
    for cluster, (icon, rec) in recs.items():
        color = CLUSTER_COLORS.get(cluster,"#fff")
        st.markdown(f"""
        <div class="info-box green" style="margin:0.3rem 0; border-left-color:{color};">
            <b>{icon} {cluster}</b><br><span style="color:#999">{rec}</span>
        </div>""", unsafe_allow_html=True)

    nav_buttons(5)
