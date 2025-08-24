import streamlit as st
from utils import load_data  
from plots import (
    kpi_total_sales, kpi_avg_sales_per_item,
    kpi_highest_selling_category, kpi_best_outlet,
    fig_sales_trend, fig_mrp_distribution,
    fig_sales_by_item_type, fig_sales_by_outlet_type, fig_sales_by_outlet_size,
    fig_location_contribution, fig_visibility_scatter,
    fig_sales_box_by_category, fig_corr_heatmap
)

# ---- Page config & Header ----------------------------------------------------
st.set_page_config(
    page_title="Sales Insights Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Sales Insights Dashboard")
st.write("Welcome! This dashboard helps track performance, customers, and revenue.")

# NOTE: Altair dark theme affects only Altair charts; we use Plotly here.
# If you later add Altair charts, you can enable its theme:
# import altair as alt; alt.themes.enable("dark")

# ---- Data loading (cached) ---------------------------------------------------
df = load_data()
dff = df  # keep a separate alias for 'filtered df' if you add filters later

st.markdown("""
**Polish applied:**
- Theming via `.streamlit/config.toml`
- Caching (`@st.cache_data`) for faster reloads
- Consistent spacing, emojis, and concise titles
- Footers with ownership & version
- Ready for Streamlit Community Cloud deployment
""")

# ---- KPI Cards ---------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

total = kpi_total_sales(dff)
avg = kpi_avg_sales_per_item(dff)
best_cat = kpi_highest_selling_category(dff)   # {'category': ..., 'total_sales': ...}
best_out = kpi_best_outlet(dff)                # {'outlet': ..., 'total_sales': ...}

c1.metric("Total Sales", f"{total:,.0f}")
c2.metric("Avg Sales / Item", f"{avg:,.2f}")

# Use delta to show share-of-total (more meaningful than repeating totals)
cat_share = (best_cat["total_sales"] / total * 100) if total else 0.0
c3.metric("Top Category", best_cat["category"] or "—", delta=f"{cat_share:.1f}% of total")

out_share = (best_out["total_sales"] / total * 100) if total else 0.0
c4.metric("Best Outlet", best_out["outlet"] or "—", delta=f"{out_share:.1f}% of total")

# ---- Charts ------------------------------------------------------------------
st.subheader("Trends")
st.plotly_chart(fig_sales_trend(dff, date_col=None, freq="M"), use_container_width=True)

st.subheader("Pricing")
st.plotly_chart(fig_mrp_distribution(dff, bins=30, show_quantiles=True), use_container_width=True)

st.subheader("Comparisons")
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_sales_by_item_type(dff, top_n=None), use_container_width=True)
with col2:
    st.plotly_chart(fig_sales_by_outlet_type(dff), use_container_width=True)

st.plotly_chart(fig_sales_by_outlet_size(dff), use_container_width=True)

st.subheader("Proportions")
st.plotly_chart(fig_location_contribution(dff), use_container_width=True)

st.subheader("Drivers & Variability")
st.plotly_chart(fig_visibility_scatter(dff), use_container_width=True)
st.plotly_chart(fig_sales_box_by_category(dff, cat_col="Item_Type", log_y=False), use_container_width=True)

st.subheader("Advanced")
st.plotly_chart(fig_corr_heatmap(dff), use_container_width=True)

st.markdown("---")
st.caption(
    "© 2025 Retail Analytics | v1.0 • Deploy: Streamlit Community Cloud → New app → select your final script."
)


