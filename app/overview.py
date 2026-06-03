import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from itertools import combinations

st.set_page_config(page_title="Olist · Overview", page_icon="🛒", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0f1117; color: #e8e8e8; }
.dash-title { font-family: 'DM Serif Display', serif; font-size: 2.6rem; color: #fff; margin: 0; }
.dash-subtitle { color: #888; font-size: 0.95rem; margin-top: 0.3rem; }
.section-title {
    font-family: 'DM Serif Display', serif; font-size: 1.3rem; color: #fff;
    margin: 2rem 0 0.8rem 0; padding-bottom: 0.4rem; border-bottom: 1px solid #2a2a3a;
}
.kpi-card {
    background: #1a1d27; border: 1px solid #2a2d3a;
    border-radius: 14px; padding: 1.4rem 1.6rem; position: relative; overflow: hidden;
}
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:14px 14px 0 0; }
.kpi-card.green::before  { background: #00c07f; }
.kpi-card.blue::before   { background: #4e8ef7; }
.kpi-card.orange::before { background: #f79c4e; }
.kpi-card.purple::before { background: #a569f7; }
.kpi-label { font-size:0.78rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; color:#666; margin-bottom:0.5rem; }
.kpi-value { font-family:'DM Serif Display',serif; font-size:2rem; color:#fff; line-height:1; }
.kpi-sub   { font-size:0.8rem; color:#555; margin-top:0.35rem; }
.algo-box {
    background: #1a1d27; border: 1px solid #2a2d3a; border-left: 4px solid #4e8ef7;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 1rem;
    font-size: 0.88rem; color: #bbb; line-height: 1.8;
}
.algo-box.green { border-left-color: #00c07f; }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_all():
    sales     = pd.read_csv("data/processed/final_sales.csv")
    fact      = pd.read_csv("data/warehouse/fact_sales.csv")
    dim_prod  = pd.read_csv("data/warehouse/dim_product.csv")
    dim_date  = pd.read_csv("data/warehouse/dim_date.csv")
    dim_pay   = pd.read_csv("data/warehouse/dim_payment.csv")
    clusters  = pd.read_csv("data/warehouse/customer_clusters.csv")

    sales["order_purchase_timestamp"] = pd.to_datetime(sales["order_purchase_timestamp"])
    sales["order_month"] = sales["order_month"].astype(str)
    sales["product_category_name"] = sales["product_category_name"].fillna("unknown")
    sales["payment_type"] = sales["payment_type"].fillna("unknown")
    sales["category_clean"] = sales["product_category_name"].str.replace("_"," ").str.title()

    # Join fact với dim_product để lấy category
    fact = fact.merge(dim_prod, on="product_id", how="left")
    fact["product_category_name"] = fact["product_category_name"].fillna("unknown")
    fact["category_clean"] = fact["product_category_name"].str.replace("_"," ").str.title()

    return sales, fact, dim_date, dim_pay, clusters

try:
    df, fact, dim_date, dim_pay, clusters = load_all()
except FileNotFoundError as e:
    st.error(f"⚠️ Không tìm thấy file: {e}")
    st.stop()

orders_df = df.drop_duplicates("order_id")

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="padding:1.5rem 0 1rem 0; border-bottom:1px solid #2a2a3a; margin-bottom:1.5rem;">
    <div class="dash-title">🛒 Olist E-Commerce Dashboard</div>
    <div class="dash-subtitle">Brazilian E-Commerce · 2016–2018 · Overview</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1. KPI
# ══════════════════════════════════════════════════════════════════════════════
total_revenue   = orders_df["total_amount"].sum()
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

c1,c2,c3,c4 = st.columns(4)
kpi(c1,"green","Tổng Doanh Thu",   f"R$ {total_revenue/1e6:.2f}M","tổng giá trị đơn hàng")
kpi(c2,"blue", "Số Đơn Hàng",      f"{total_orders:,}",           "đơn hàng duy nhất")
kpi(c3,"orange","Số Khách Hàng",   f"{total_customers:,}",        "khách hàng unique")
kpi(c4,"purple","AOV",             f"R$ {avg_order_value:.2f}",   "giá trị đơn trung bình")

# ══════════════════════════════════════════════════════════════════════════════
# 2. DOANH THU THEO THÁNG
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📈 Doanh Thu Theo Tháng</div>', unsafe_allow_html=True)

monthly = (orders_df.groupby("order_month")["total_amount"].sum()
           .reset_index().rename(columns={"order_month":"Tháng","total_amount":"Doanh Thu (R$)"})
           .sort_values("Tháng"))
monthly = monthly[monthly["Tháng"].between("2017-01","2018-08")]

fig_line = px.area(monthly, x="Tháng", y="Doanh Thu (R$)",
                   color_discrete_sequence=["#00c07f"], template="plotly_dark")
fig_line.update_traces(fill="tozeroy", fillcolor="rgba(0,192,127,0.12)", line=dict(width=2.5))
fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                       margin=dict(l=0,r=0,t=10,b=0),
                       xaxis=dict(showgrid=False, tickangle=-30),
                       yaxis=dict(gridcolor="#1f2230"), height=280)
st.plotly_chart(fig_line, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 3. TOP CATEGORY + STATE
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns(2)

with col_left:
    st.markdown('<div class="section-title">📦 Top 10 Category Bán Chạy</div>', unsafe_allow_html=True)
    cat = (df.drop_duplicates(["order_id","product_category_name"])
           .groupby("category_clean")["order_id"].count()
           .nlargest(10).reset_index()
           .rename(columns={"category_clean":"Category","order_id":"Số Đơn"})
           .sort_values("Số Đơn"))
    fig_cat = px.bar(cat, x="Số Đơn", y="Category", orientation="h",
                     color="Số Đơn", color_continuous_scale=["#1a3a5c","#4e8ef7"],
                     template="plotly_dark")
    fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                          margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False,
                          yaxis=dict(showgrid=False), xaxis=dict(gridcolor="#1f2230"), height=360)
    st.plotly_chart(fig_cat, use_container_width=True)

with col_right:
    st.markdown('<div class="section-title">🗺️ Phân Bổ Đơn Hàng Theo Bang</div>', unsafe_allow_html=True)
    state = (orders_df.groupby("customer_state")["order_id"].count()
             .reset_index().rename(columns={"customer_state":"Bang","order_id":"Số Đơn"})
             .sort_values("Số Đơn", ascending=False).head(12))
    fig_state = px.bar(state, x="Bang", y="Số Đơn", color="Số Đơn",
                       color_continuous_scale=["#2a1a3a","#a569f7"], template="plotly_dark")
    fig_state.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                            margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False,
                            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"), height=360)
    st.plotly_chart(fig_state, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 4. THỐNG KÊ MÔ TẢ
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🔍 Thống Kê Mô Tả Dữ Liệu Processed</div>', unsafe_allow_html=True)

num_cols = ["price","freight_value","total_amount","review_score","delivery_days"]
desc = df[num_cols].describe().round(2)
desc.index = ["Số dòng","Mean","Std","Min","25%","Median","75%","Max"]
desc.columns = ["Giá SP (R$)","Phí Ship (R$)","Tổng TT (R$)","Review Score","Giao hàng (ngày)"]
st.dataframe(desc.style.format("{:,.2f}").background_gradient(cmap="Blues", axis=1),
             use_container_width=True)

ca, cb, cc = st.columns(3)
ca.metric("Tổng số dòng", f"{len(df):,}")
cb.metric("Số cột", f"{df.shape[1]}")
cc.metric("Tỉ lệ missing", f"{df.isnull().sum().sum()/df.size*100:.2f}%")

with st.expander("📋 Chi tiết missing values theo cột"):
    miss = df.isnull().sum().reset_index()
    miss.columns = ["Cột","Số dòng thiếu"]
    miss["Tỉ lệ (%)"] = (miss["Số dòng thiếu"]/len(df)*100).round(2)
    st.dataframe(miss[miss["Số dòng thiếu"]>0], use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# 5. ICEBERG CUBE — BUC TOP-DOWN (từ fact_sales thực)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🧊 Iceberg Cube — BUC Top-Down</div>', unsafe_allow_html=True)

MIN_SUPPORT = 200

st.markdown(f"""
<div class="algo-box">
    <b>Cơ chế BUC Top-Down:</b><br>
    1. Bắt đầu từ cuboid <b>ALL*</b> — tổng toàn bộ {total_orders:,} đơn<br>
    2. Duyệt xuống từng tổ hợp dimension: <code>Category</code> · <code>State</code> · <code>Payment</code> → tổ hợp 2-dim, 3-dim<br>
    3. Với mỗi cell: nếu <code>order_count &lt; {MIN_SUPPORT}</code> → <b>cắt tỉa</b>, bỏ qua nhánh con<br>
    4. Giữ lại các cell thỏa điều kiện Iceberg → tập trung vào dữ liệu có nghĩa thống kê
</div>
""", unsafe_allow_html=True)

@st.cache_data
def build_cube(fact_df, min_sup):
    DIMS = {"Category":"category_clean", "State":"customer_state", "Payment":"payment_type"}
    # join state từ final_sales
    state_map = df[["customer_id","customer_state"]].drop_duplicates("customer_id")
    fact_aug = fact_df.merge(state_map, on="customer_id", how="left")
    fact_aug["customer_state"] = fact_aug["customer_state"].fillna("unknown")
    fact_aug = fact_aug.drop_duplicates("order_id")

    results = []
    # ALL* apex
    apex = pd.DataFrame([{
        "cuboid":"ALL*","level":0,"label":"ALL",
        "order_count": len(fact_aug),
        "total_revenue": fact_aug["total_amount"].sum(),
        "avg_review": fact_aug["review_score"].mean(),
    }])
    results.append(apex)

    for r in range(1, len(DIMS)+1):
        for combo in combinations(DIMS.keys(), r):
            cols = [DIMS[d] for d in combo]
            agg = fact_aug.groupby(cols).agg(
                order_count   = ("order_id","count"),
                total_revenue = ("total_amount","sum"),
                avg_review    = ("review_score","mean"),
            ).reset_index()
            agg = agg[agg["order_count"] >= min_sup].copy()
            if agg.empty: continue
            agg["cuboid"] = " × ".join(combo)
            agg["level"]  = len(combo)
            agg["label"]  = agg[cols].apply(lambda r: " | ".join(r.astype(str)), axis=1)
            results.append(agg)
    return results

with st.spinner("Đang tính Iceberg Cube từ fact_sales..."):
    cuboids = build_cube(fact, MIN_SUPPORT)

cell_counts = {}
for c in cuboids:
    name = c["cuboid"].iloc[0]
    cell_counts[name] = len(c)
total_cells = sum(v for k,v in cell_counts.items() if k != "ALL*")

# Lattice Sankey
DIMS_LIST = ["Category","State","Payment"]
lattice_nodes = ["ALL*"] + [
    " × ".join(combo)
    for r in range(1, len(DIMS_LIST)+1)
    for combo in combinations(DIMS_LIST, r)
]
node_labels, node_colors = [], []
for n in lattice_nodes:
    cnt = cell_counts.get(n, 0)
    node_labels.append(f"{n}<br>({cnt} cells)" if cnt else f"{n}<br>(pruned ✗)")
    node_colors.append("#4e8ef7" if n=="ALL*" else ("#00c07f" if cnt>0 else "#2a2a3a"))

source, target, value = [], [], []
for i, n in enumerate(lattice_nodes):
    n_set = set(n.replace("ALL*","").replace(" × ","||").split("||")) - {""}
    for j, m in enumerate(lattice_nodes):
        if i==j: continue
        m_set = set(m.replace("ALL*","").replace(" × ","||").split("||")) - {""}
        if len(m_set)==len(n_set)+1 and n_set.issubset(m_set):
            source.append(i); target.append(j)
            value.append(max(cell_counts.get(m,1),1))

col_l, col_r = st.columns([3,2])
with col_l:
    st.markdown("**Lattice Cuboid — Cây duyệt BUC**")
    fig_lat = go.Figure(go.Sankey(
        node=dict(label=node_labels, color=node_colors, pad=15, thickness=18,
                  line=dict(color="#0f1117", width=0.5)),
        link=dict(source=source, target=target, value=value,
                  color="rgba(78,142,247,0.12)")
    ))
    fig_lat.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(color="#ccc",family="DM Sans",size=11),
                          height=340, margin=dict(l=0,r=0,t=10,b=0))
    st.plotly_chart(fig_lat, use_container_width=True)

with col_r:
    st.markdown("**Thống kê Iceberg Cube**")
    st.metric("Tổng cell giữ lại", f"{total_cells:,}")
    st.metric("Min support", MIN_SUPPORT)
    st.metric("Số cuboid có dữ liệu", len(cuboids))
    cats   = df["category_clean"].nunique()
    states = df["customer_state"].nunique()
    pays   = df["payment_type"].nunique()
    theoretical = cats+states+pays+cats*states+cats*pays+states*pays+cats*states*pays
    st.metric("Tỉ lệ giữ lại", f"{total_cells/theoretical*100:.1f}%",
              f"/{theoretical:,} cells lý thuyết", delta_color="off")

# Top 10 cell nổi bật
st.markdown("**Top 10 Cell Nổi Bật (order_count cao nhất)**")
all_cells = pd.concat(
    [c[["cuboid","label","order_count","total_revenue","avg_review"]]
     for c in cuboids if "label" in c.columns],
    ignore_index=True
)
top10 = all_cells.nlargest(10,"order_count").copy()
top10["total_revenue"] = top10["total_revenue"].map("R$ {:,.0f}".format)
top10["avg_review"]    = top10["avg_review"].map("{:.2f}".format)
top10["order_count"]   = top10["order_count"].map("{:,}".format)
top10.columns = ["Cuboid","Cell","Số đơn","Doanh thu","Review TB"]
st.dataframe(top10, use_container_width=True, hide_index=True)

# Heatmap Category × State
st.markdown("**Heatmap Category × State (Top 10 × Top 10)**")
state_map2 = df[["customer_id","customer_state"]].drop_duplicates("customer_id")
fact_aug2 = fact.merge(state_map2, on="customer_id", how="left").drop_duplicates("order_id")
pivot_data = fact_aug2.groupby(["category_clean","customer_state"]).agg(
    order_count=("order_id","count")).reset_index()
pivot_data = pivot_data[pivot_data["order_count"]>=MIN_SUPPORT]
top_cat   = pivot_data.groupby("category_clean")["order_count"].sum().nlargest(10).index
top_state = pivot_data.groupby("customer_state")["order_count"].sum().nlargest(10).index
heat_data = pivot_data[pivot_data["category_clean"].isin(top_cat) &
                       pivot_data["customer_state"].isin(top_state)]
heat_pivot = heat_data.pivot_table(index="category_clean", columns="customer_state",
                                   values="order_count", fill_value=0)
fig_heat = px.imshow(heat_pivot, color_continuous_scale="Blues",
                     template="plotly_dark", aspect="auto",
                     labels={"color":"Số đơn","x":"Bang","y":"Category"})
fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                       margin=dict(l=0,r=0,t=10,b=0), height=380)
st.plotly_chart(fig_heat, use_container_width=True)
st.caption(f"Cells có order_count < {MIN_SUPPORT} đã bị cắt tỉa theo điều kiện Iceberg")

# ══════════════════════════════════════════════════════════════════════════════
# 6. CLUSTERING — dùng data thực từ customer_clusters.csv
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">👥 Clustering — RFM & K-Means</div>', unsafe_allow_html=True)

st.markdown("""
<div class="algo-box green">
    <b>Cơ chế RFM + K-Means:</b><br>
    1. Tính <b>Recency</b> (ngày kể từ đơn cuối) · <b>Frequency</b> (số đơn) · <b>Monetary</b> (tổng chi tiêu) cho mỗi khách<br>
    2. Chuẩn hóa bằng <b>StandardScaler</b> → giảm chiều bằng <b>PCA</b> để visualize<br>
    3. Chọn k tối ưu bằng <b>Elbow Method</b> + <b>Silhouette Score</b><br>
    4. Gán nhãn cluster → phân tích đặc trưng từng nhóm khách hàng
</div>
""", unsafe_allow_html=True)

CLUSTER_COLORS = {
    "Khách hàng tiềm năng":     "#4e8ef7",
    "Khách hàng giá trị thấp":  "#f79c4e",
    "Khách hàng giá trị cao":   "#00c07f",
    "Khách hàng ít hoạt động":  "#a569f7",
}

# Scatter PCA 2D (dùng pca_1/pca_2 từ file thực)
st.markdown("**Scatter Plot PCA — Phân Bổ Các Cluster**")
sample = clusters.sample(min(4000, len(clusters)), random_state=42)
fig_scatter = px.scatter(
    sample, x="pca_1", y="pca_2",
    color="cluster_name",
    color_discrete_map=CLUSTER_COLORS,
    template="plotly_dark", opacity=0.55,
    labels={"pca_1":"PCA 1","pca_2":"PCA 2","cluster_name":"Cluster"},
    hover_data={"recency":True,"frequency":True,"monetary":":.0f","pca_1":False,"pca_2":False},
)
fig_scatter.update_traces(marker=dict(size=4))
fig_scatter.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
    margin=dict(l=0,r=0,t=20,b=0), height=420,
    xaxis=dict(showgrid=False), yaxis=dict(showgrid=False),
    legend=dict(bgcolor="rgba(26,29,39,0.9)", bordercolor="#2a2d3a", title="Cluster")
)
st.plotly_chart(fig_scatter, use_container_width=True)

# Profile bảng từng cluster
st.markdown("**Profile Từng Cluster**")
profile = clusters.groupby("cluster_name").agg(
    Số_khách        = ("customer_unique_id","count"),
    Recency_TB      = ("recency",           "mean"),
    Frequency_TB    = ("frequency",         "mean"),
    Monetary_TB     = ("monetary",          "mean"),
    AOV_TB          = ("avg_order_value",   "mean"),
    Review_TB       = ("avg_review_score",  "mean"),
    Delivery_TB     = ("avg_delivery_days", "mean"),
).round(1).reset_index()
profile["Tỉ lệ (%)"] = (profile["Số_khách"]/profile["Số_khách"].sum()*100).round(1)
profile = profile.rename(columns={
    "cluster_name":"Cluster","Số_khách":"Số khách",
    "Recency_TB":"Recency TB (ngày)","Frequency_TB":"Frequency TB",
    "Monetary_TB":"Monetary TB (R$)","AOV_TB":"AOV TB (R$)",
    "Review_TB":"Review TB","Delivery_TB":"Giao hàng TB (ngày)"
})
st.dataframe(
    profile.style
        .format({"Recency TB (ngày)":"{:.1f}","Frequency TB":"{:.1f}",
                 "Monetary TB (R$)":"R$ {:,.1f}","AOV TB (R$)":"R$ {:,.1f}",
                 "Review TB":"{:.2f}","Giao hàng TB (ngày)":"{:.1f}","Tỉ lệ (%)":"{:.1f}%"})
        .background_gradient(subset=["Monetary TB (R$)"], cmap="Purples"),
    use_container_width=True, hide_index=True
)

# Bar chart phân bổ
col_b1, col_b2 = st.columns(2)
with col_b1:
    fig_bar_c = px.bar(
        profile, x="Cluster", y="Số khách",
        color="Cluster", color_discrete_map=CLUSTER_COLORS,
        text="Tỉ lệ (%)", template="plotly_dark",
    )
    fig_bar_c.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_bar_c.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                            margin=dict(l=0,r=0,t=20,b=0), height=320, showlegend=False,
                            xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"),
                            title="Phân bổ số khách theo cluster")
    st.plotly_chart(fig_bar_c, use_container_width=True)

with col_b2:
    fig_mon = px.bar(
        profile, x="Cluster", y="Monetary TB (R$)",
        color="Cluster", color_discrete_map=CLUSTER_COLORS,
        template="plotly_dark",
    )
    fig_mon.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,29,39,1)",
                          margin=dict(l=0,r=0,t=20,b=0), height=320, showlegend=False,
                          xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#1f2230"),
                          title="Monetary trung bình theo cluster")
    st.plotly_chart(fig_mon, use_container_width=True)

# Radar chart profile so sánh các cluster
st.markdown("**Radar Chart — So Sánh Đặc Trưng Các Cluster**")
radar_metrics = ["Recency TB (ngày)","Frequency TB","Monetary TB (R$)","Review TB","Giao hàng TB (ngày)"]
radar_df = profile[["Cluster"] + radar_metrics].copy()
# Normalize 0-1 cho radar
for col in radar_metrics:
    mn, mx = radar_df[col].min(), radar_df[col].max()
    radar_df[col] = (radar_df[col]-mn)/(mx-mn+1e-9)

fig_radar = go.Figure()
for _, row in radar_df.iterrows():
    vals = [row[m] for m in radar_metrics] + [row[radar_metrics[0]]]
    cats = radar_metrics + [radar_metrics[0]]
    fig_radar.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill="toself", name=row["Cluster"],
        line_color=CLUSTER_COLORS.get(row["Cluster"],"#fff"),
        fillcolor=CLUSTER_COLORS.get(row["Cluster"],"#fff").replace("#","rgba(") + ",0.15)"
                  if "#" not in CLUSTER_COLORS.get(row["Cluster"],"") else
                  f"rgba(78,142,247,0.1)",
        opacity=0.85,
    ))
fig_radar.update_layout(
    polar=dict(
        bgcolor="rgba(26,29,39,1)",
        radialaxis=dict(visible=True, range=[0,1], gridcolor="#2a2d3a", tickfont=dict(color="#666")),
        angularaxis=dict(gridcolor="#2a2d3a", tickfont=dict(color="#ccc")),
    ),
    paper_bgcolor="rgba(0,0,0,0)",
    template="plotly_dark",
    legend=dict(bgcolor="rgba(26,29,39,0.9)", bordercolor="#2a2d3a"),
    height=420, margin=dict(l=40,r=40,t=20,b=20),
    showlegend=True,
)
st.plotly_chart(fig_radar, use_container_width=True)
st.caption("Các chỉ số đã được chuẩn hóa về [0,1] để so sánh tương đối giữa các cluster")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border-color:#2a2a3a; margin-top:2rem;">
<p style="text-align:center; color:#444; font-size:0.8rem;">
    Data Mining Project · Olist Brazilian E-Commerce · Nhóm DM
</p>
""", unsafe_allow_html=True)
