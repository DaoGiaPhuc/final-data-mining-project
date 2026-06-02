import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Olist · Overview",
    page_icon="🛒",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Nền tổng thể */
.stApp {
    background: #0f1117;
    color: #e8e8e8;
}

/* Header */
.dash-header {
    padding: 2rem 0 1rem 0;
    border-bottom: 1px solid #2a2a3a;
    margin-bottom: 2rem;
}
.dash-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.6rem;
    color: #ffffff;
    letter-spacing: -0.5px;
    margin: 0;
}
.dash-subtitle {
    color: #888;
    font-size: 0.95rem;
    margin-top: 0.3rem;
}

/* KPI Cards */
.kpi-card {
    background: #1a1d27;
    border: 1px solid #2a2d3a;
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}
.kpi-card.green::before  { background: #00c07f; }
.kpi-card.blue::before   { background: #4e8ef7; }
.kpi-card.orange::before { background: #f79c4e; }
.kpi-card.purple::before { background: #a569f7; }

.kpi-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #666;
    margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #fff;
    line-height: 1;
}
.kpi-sub {
    font-size: 0.8rem;
    color: #555;
    margin-top: 0.35rem;
}

/* Section titles */
.section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #fff;
    margin: 2rem 0 1rem 0;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #2a2a3a;
}

/* Plotly chart bg matching */
.js-plotly-plot .plotly { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/processed/final_sales.csv")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["order_month"] = df["order_month"].astype(str)
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("⚠️ Không tìm thấy `data/processed/final_sales.csv`. Hãy chạy notebook tiền xử lý trước.")
    st.stop()

# ── Derived metrics ───────────────────────────────────────────────────────────
orders_df = df.drop_duplicates("order_id")

total_revenue  = orders_df["total_amount"].sum()
total_orders   = orders_df["order_id"].nunique()
total_customers = df["customer_unique_id"].nunique()
avg_order_value = total_revenue / total_orders if total_orders else 0

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="dash-header">
    <div class="dash-title">🛒 Olist E-Commerce Dashboard</div>
    <div class="dash-subtitle">Brazilian E-Commerce · 2016 – 2018 · Overview</div>
</div>
""", unsafe_allow_html=True)

# ── KPI Row ───────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

def kpi(col, color, label, value, sub):
    col.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi(c1, "green",  "Tổng Doanh Thu",  f"R$ {total_revenue/1e6:.2f}M",  "tổng giá trị đơn hàng")
kpi(c2, "blue",   "Số Đơn Hàng",     f"{total_orders:,}",              "đơn hàng duy nhất")
kpi(c3, "orange", "Số Khách Hàng",   f"{total_customers:,}",           "khách hàng unique")
kpi(c4, "purple", "AOV (Avg Order)",  f"R$ {avg_order_value:.2f}",      "giá trị đơn trung bình")

# ── Revenue by Month ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📈 Doanh Thu Theo Tháng</div>', unsafe_allow_html=True)

monthly = (
    orders_df.groupby("order_month")["total_amount"]
    .sum()
    .reset_index()
    .rename(columns={"order_month": "Tháng", "total_amount": "Doanh Thu (R$)"})
    .sort_values("Tháng")
)
# Lọc bỏ tháng đầu/cuối có thể bị lệch
monthly = monthly[monthly["Tháng"].between("2017-01", "2018-08")]

fig_line = px.area(
    monthly,
    x="Tháng", y="Doanh Thu (R$)",
    color_discrete_sequence=["#00c07f"],
    template="plotly_dark",
)
fig_line.update_traces(
    fill="tozeroy",
    fillcolor="rgba(0,192,127,0.12)",
    line=dict(width=2.5),
)
fig_line.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(26,29,39,1)",
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(showgrid=False, tickangle=-30),
    yaxis=dict(gridcolor="#1f2230"),
    height=300,
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Two-column: Top Categories + State Distribution ───────────────────────────
col_left, col_right = st.columns(2)

# Top 10 Categories
with col_left:
    st.markdown('<div class="section-title">📦 Top 10 Category Bán Chạy</div>', unsafe_allow_html=True)

    cat = (
        df.drop_duplicates(["order_id", "product_category_name"])
        .groupby("product_category_name")["order_id"]
        .count()
        .nlargest(10)
        .reset_index()
        .rename(columns={"product_category_name": "Category", "order_id": "Số Đơn"})
        .sort_values("Số Đơn")
    )
    # Format tên đẹp hơn
    cat["Category"] = cat["Category"].str.replace("_", " ").str.title()

    fig_bar = px.bar(
        cat, x="Số Đơn", y="Category",
        orientation="h",
        color="Số Đơn",
        color_continuous_scale=["#1a3a5c", "#4e8ef7"],
        template="plotly_dark",
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,29,39,1)",
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
        yaxis=dict(showgrid=False),
        xaxis=dict(gridcolor="#1f2230"),
        height=380,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# State Distribution
with col_right:
    st.markdown('<div class="section-title">🗺️ Phân Bổ Đơn Hàng Theo Bang</div>', unsafe_allow_html=True)

    state = (
        orders_df.groupby("customer_state")["order_id"]
        .count()
        .reset_index()
        .rename(columns={"customer_state": "Bang", "order_id": "Số Đơn"})
        .sort_values("Số Đơn", ascending=False)
        .head(12)
    )

    fig_pie = px.bar(
        state, x="Bang", y="Số Đơn",
        color="Số Đơn",
        color_continuous_scale=["#2a1a3a", "#a569f7"],
        template="plotly_dark",
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,29,39,1)",
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_showscale=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="#1f2230"),
        height=380,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#2a2a3a; margin-top:2rem;">
<p style="text-align:center; color:#444; font-size:0.8rem;">
    Data Mining Project · Olist Brazilian E-Commerce Dataset · Nhóm DM
</p>
""", unsafe_allow_html=True)
