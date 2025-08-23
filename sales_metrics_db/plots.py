# plots.py
import pandas as pd
import plotly.express as px

# ---------- shared styling helpers ----------

DEFAULT_TEMPLATE = "plotly_white"

def _style_fig(fig, title=None, height=360):
    """Uniform look & feel for all charts."""
    if title:
        fig.update_layout(title=dict(text=title, x=0.02, xanchor="left"))
    fig.update_layout(
        template=DEFAULT_TEMPLATE,
        height=height,
        margin=dict(t=60, r=16, b=16, l=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="closest",
        bargap=0.15,
        font=dict(size=12),
    )
    return fig

def _ensure_cols(df: pd.DataFrame, cols):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


# ---------- KPI cards (numbers to show in st.metric) ----------

def kpi_total_sales(df: pd.DataFrame) -> float:
    """Total sales across all rows."""
    _ensure_cols(df, ["Item_Outlet_Sales"])
    return float(pd.to_numeric(df["Item_Outlet_Sales"], errors="coerce").sum())

def kpi_avg_sales_per_item(df: pd.DataFrame) -> float:
    """Average sales per row/item."""
    _ensure_cols(df, ["Item_Outlet_Sales"])
    s = pd.to_numeric(df["Item_Outlet_Sales"], errors="coerce")
    return float(s.mean())

def kpi_highest_selling_category(df: pd.DataFrame, cat_col: str = "Item_Type") -> dict:
    """Highest selling product category (by total sales)."""
    _ensure_cols(df, ["Item_Outlet_Sales", cat_col])
    g = (
        df.groupby(cat_col, dropna=False)["Item_Outlet_Sales"]
        .sum()
        .sort_values(ascending=False)
    )
    if g.empty:
        return {"category": None, "total_sales": 0.0}
    return {"category": g.index[0], "total_sales": float(g.iloc[0])}

def kpi_best_outlet(df: pd.DataFrame) -> dict:
    """Best performing outlet (Outlet_Identifier if present, else Outlet_Type)."""
    outlet_col = "Outlet_Identifier" if "Outlet_Identifier" in df.columns else "Outlet_Type"
    _ensure_cols(df, ["Item_Outlet_Sales", outlet_col])
    g = (
        df.groupby(outlet_col, dropna=False)["Item_Outlet_Sales"]
        .sum()
        .sort_values(ascending=False)
    )
    if g.empty:
        return {"outlet": None, "total_sales": 0.0}
    return {"outlet": g.index[0], "total_sales": float(g.iloc[0])}


# ---------- Line chart (trend) ----------

def fig_sales_trend(
    df: pd.DataFrame, date_col: str | None = None, freq: str = "M"
):
    """
    Sales trend over time.
    - If `date_col` provided and exists: group by period (freq='M','Q','Y').
    - Else if 'Outlet_Establishment_Year' exists: line over that year.
    - Else: fallback to index order (not a real time series, but shows progression).
    """
    _ensure_cols(df, ["Item_Outlet_Sales"])
    s = pd.to_numeric(df["Item_Outlet_Sales"], errors="coerce")

    if date_col and date_col in df.columns:
        dt = pd.to_datetime(df[date_col], errors="coerce")
        d = (
            pd.DataFrame({"_dt": dt, "sales": s})
            .dropna(subset=["_dt"])
            .groupby(pd.Grouper(key="_dt", freq=freq))
            .sum()
            .reset_index()
            .rename(columns={"sales": "total_sales"})
        )
        fig = px.line(d, x="_dt", y="total_sales", markers=True)
        return _style_fig(fig, f"Sales Trend ({freq}-periods)")
    elif "Outlet_Establishment_Year" in df.columns:
        d = (
            df.assign(_yr=pd.to_numeric(df["Outlet_Establishment_Year"], errors="coerce"))
            .dropna(subset=["_yr"])
            .groupby("_yr")["Item_Outlet_Sales"].sum()
            .reset_index(name="total_sales")
        )
        fig = px.line(d, x="_yr", y="total_sales", markers=True)
        fig.update_xaxes(title="Year")
        return _style_fig(fig, "Sales by Outlet Establishment Year")
    else:
        d = (
            pd.DataFrame({"idx": range(len(df)), "sales": s})
            .groupby("idx")
            .sum()
            .reset_index()
            .rename(columns={"sales": "total_sales"})
        )
        fig = px.line(d, x="idx", y="total_sales", markers=True)
        fig.update_xaxes(title="Index (no date column found)")
        return _style_fig(fig, "Sales Trend (Index Order)")


# ---------- Sales distribution by price (Item_MRP) ----------

def fig_mrp_distribution(df: pd.DataFrame, bins: int = 30, show_quantiles: bool = True):
    """
    Histogram of Item_MRP to reveal price clusters; quantile lines highlight 'sweet spots'.
    """
    _ensure_cols(df, ["Item_MRP"])
    fig = px.histogram(df, x="Item_MRP", nbins=bins, opacity=0.9)
    fig.update_yaxes(title="Count")
    if show_quantiles and df["Item_MRP"].notna().any():
        q = df["Item_MRP"].quantile([0.25, 0.5, 0.75]).to_dict()
        labels = {0.25: "Q1", 0.5: "Median", 0.75: "Q3"}
        for quant, label in q.items():
            fig.add_vline(
                x=label,
                line_dash="dot",
                opacity=0.6,
                annotation_text=labels[float(quant)],
                annotation_position="top",
            )
    return _style_fig(fig, "Sales Distribution by Item_MRP (Pricing Landscape)")


# ---------- Bar charts (comparisons) ----------

def _bar_series(df: pd.DataFrame, group_col: str, top_n: int | None = None, horizontal=True):
    _ensure_cols(df, ["Item_Outlet_Sales", group_col])
    g = (
        df.groupby(group_col, dropna=False)["Item_Outlet_Sales"]
        .sum()
        .sort_values(ascending=False)
        .reset_index(name="total_sales")
    )
    if top_n:
        g = g.head(top_n)
    # preserve sort order in categorical axis
    order = g[group_col].astype(str).tolist()

    if horizontal:
        fig = px.bar(
            g, x="total_sales", y=group_col,
            orientation="h",
            category_orders={group_col: order},
            labels={"total_sales": "Total Sales"}
        )
    else:
        fig = px.bar(
            g, x=group_col, y="total_sales",
            category_orders={group_col: order},
            labels={"total_sales": "Total Sales"}
        )
    return fig

def fig_sales_by_item_type(df: pd.DataFrame, top_n: int | None = None):
    fig = _bar_series(df, "Item_Type", top_n=top_n, horizontal=True)
    return _style_fig(fig, "Total Sales by Item Type")

def fig_sales_by_outlet_type(df: pd.DataFrame):
    fig = _bar_series(df, "Outlet_Type", top_n=None, horizontal=False)
    return _style_fig(fig, "Total Sales by Outlet Type")

def fig_sales_by_outlet_size(df: pd.DataFrame):
    fig = _bar_series(df, "Outlet_Size", top_n=None, horizontal=False)
    return _style_fig(fig, "Total Sales by Outlet Size")


# ---------- Pie / Donut (proportions) ----------

def fig_location_contribution(df: pd.DataFrame, hole: float = 0.5):
    """
    Sales share by Outlet_Location_Type (Tier 1/2/3).
    """
    _ensure_cols(df, ["Item_Outlet_Sales", "Outlet_Location_Type"])
    g = (
        df.groupby("Outlet_Location_Type", dropna=False)["Item_Outlet_Sales"]
        .sum()
        .reset_index(name="total_sales")
    )
    fig = px.pie(g, names="Outlet_Location_Type", values="total_sales", hole=hole)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return _style_fig(fig, "Sales Share by Location (Tier)", height=380)


# ---------- Scatter (visibility impact) ----------

def fig_visibility_scatter(df: pd.DataFrame, color: str = "Item_Type"):
    """
    Item_Visibility vs Item_Outlet_Sales, colored by product category.
    """
    _ensure_cols(df, ["Item_Visibility", "Item_Outlet_Sales"])
    hover = ["Outlet_Type", "Outlet_Location_Type"] if "Outlet_Type" in df.columns and "Outlet_Location_Type" in df.columns else None
    fig = px.scatter(
        df,
        x="Item_Visibility",
        y="Item_Outlet_Sales",
        color=color if color in df.columns else None,
        opacity=0.6,
        hover_data=hover,
        trendline=None,  # set to 'ols' if statsmodels installed and you want a fitted line
    )
    fig.update_xaxes(title="Item Visibility")
    fig.update_yaxes(title="Item Outlet Sales")
    return _style_fig(fig, "Visibility vs Sales (Scatter)")


# ---------- Box plot (spread & outliers) ----------

def fig_sales_box_by_category(df: pd.DataFrame, cat_col: str = "Item_Type", log_y: bool = False):
    """
    Distribution of sales per category to inspect spread & outliers.
    """
    _ensure_cols(df, ["Item_Outlet_Sales", cat_col])
    fig = px.box(df, x=cat_col, y="Item_Outlet_Sales", points=False)
    if log_y:
        fig.update_yaxes(type="log")
    fig.update_xaxes(title=cat_col.replace("_", " "))
    fig.update_yaxes(title="Item Outlet Sales")
    return _style_fig(fig, f"Sales Distribution by {cat_col} (Box Plot)", height=420)


# ---------- Heatmap (optional advanced) ----------

def fig_corr_heatmap(
    df: pd.DataFrame,
    cols: list[str] | None = None,
):
    """
    Correlation matrix of selected numerical columns.
    Default: Item_Weight, Item_MRP, Item_Visibility, Item_Outlet_Sales
    """
    if cols is None:
        cols = ["Item_Weight", "Item_MRP", "Item_Visibility", "Item_Outlet_Sales"]
    # keep only available numeric columns
    cols = [c for c in cols if c in df.columns]
    if not cols:
        raise ValueError("No valid numeric columns found for correlation heatmap.")
    corr = df[cols].apply(pd.to_numeric, errors="coerce").corr().round(2)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu",
        zmin=-1,
        zmax=1,
        origin="lower",
        aspect="auto",
    )
    fig.update_xaxes(side="bottom")
    return _style_fig(fig, "Correlation Heatmap", height=420)
