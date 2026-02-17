import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import yaml
import subprocess

# -----------------------------
# 1. Page Setup
# -----------------------------
st.set_page_config(page_title="Music Store Executive Dashboard", layout="wide")
st.title("🎵 Music Store Executive Dashboard")
st.markdown("Interactive KPIs, trends, top customers, with executive visuals & one-click dbt refresh")

# -----------------------------
# 2. Connect to DuckDB via dbt
# -----------------------------
dbt_profiles_path = os.path.expanduser("~/.dbt/profiles.yml")
with open(dbt_profiles_path) as f:
    profiles = yaml.safe_load(f)

profile_name = list(profiles.keys())[0]
target_name = profiles[profile_name]['target']
duckdb_path = profiles[profile_name]['outputs'][target_name]['path']
conn = duckdb.connect(duckdb_path)

# -----------------------------
# 3. Refresh dbt & Load Data
# -----------------------------
def run_dbt_and_reload():
    st.info("Running dbt models...")
    subprocess.run(["dbt", "run"], check=True)
    st.success("dbt run completed, reloading data...")
    return conn.execute("SELECT * FROM fct_music_kpi").df()

if st.button("🔄 Refresh Data (Run dbt)"):
    df = run_dbt_and_reload()
else:
    @st.cache_data
    def load_data():
        return conn.execute("SELECT * FROM fct_music_kpi").df()
    df = load_data()

# -----------------------------
# 4. Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")
top_n_countries = st.sidebar.slider("Top N countries", 1, 10, 5)
selected_country = st.sidebar.selectbox("Select Country", df['country'].unique())
selected_genre = st.sidebar.selectbox("Select Genre", df['genre_name'].unique())

top_countries_df = df[df['country_rank'] <= top_n_countries]
country_df = top_countries_df[top_countries_df['country'] == selected_country]

# -----------------------------
# 5. KPI Cards with Safe Defaults
# -----------------------------
st.subheader(f"Top KPIs for {selected_country}")

def growth_metric(val):
    if val is None or pd.isna(val):
        return "N/A", "gray"
    elif val > 0:
        return f"{val*100:.2f}% ↑", "green"
    elif val < 0:
        return f"{val*100:.2f}% ↓", "red"
    else:
        return "0%", "gray"

col1, col2, col3, col4, col5 = st.columns(5)

# --- Safe KPI values with fallbacks ---
country_revenue = country_df['country_revenue'].sum() if 'country_revenue' in country_df.columns else 0
top_genre_revenue = country_df['genre_revenue_country'].max() if 'genre_revenue_country' in country_df.columns else 0
top_ltv = country_df['top_customer_ltv'].max() if 'top_customer_ltv' in country_df.columns else 0
top_contrib = country_df['top_customer_contribution_pct'].max() if 'top_customer_contribution_pct' in country_df.columns else 0
yoy = country_df['country_yoy_growth_pct'].mean() if 'country_yoy_growth_pct' in country_df.columns else 0

col1.metric("Country Revenue", f"${country_revenue:,.0f}")
col2.metric("Top Genre Revenue", f"${top_genre_revenue:,.0f}")
col3.metric("Top Customer LTV", f"${top_ltv:,.0f}")
col4.metric("Top Customer Contribution", f"{top_contrib*100:.2f}%")
yoy_text, yoy_color = growth_metric(yoy)
col5.metric("Country YoY Growth", yoy_text, delta_color=yoy_color)

# -----------------------------
## -----------------------------
# 6. Top Genres per Country Chart
# -----------------------------
st.subheader("Top Genres per Country (Top 5)")

if 'genre_revenue_country' in country_df.columns:

    # Take top 5 genres safely
    top_genres = (
        country_df
        .sort_values("genre_revenue_country", ascending=False)
        .drop_duplicates(subset=["genre_name"])
        .head(5)
        .copy()
    )

    # Create safe label column INSIDE dataframe
    if 'genre_market_share_pct' in top_genres.columns:
        top_genres["market_share_label"] = (
            top_genres["genre_market_share_pct"] * 100
        ).round(1).astype(str) + "%"
    else:
        top_genres["market_share_label"] = ""

    hover_cols = [
        c for c in [
            "genre_name",
            "genre_revenue_country",
            "genre_market_share_pct",
            "genre_yoy_growth_pct"
        ]
        if c in top_genres.columns
    ]

    genre_chart = px.bar(
        top_genres,
        x="genre_name",
        y="genre_revenue_country",
        color="genre_revenue_country",
        text="market_share_label",
        hover_data=hover_cols
    )

    genre_chart.update_layout(showlegend=False)

    st.plotly_chart(genre_chart, width='stretch')

# -----------------------------
# 7. Country Revenue Trend with MoM & YTD
# -----------------------------
st.subheader("Country Revenue Trend")
revenue_cols = ['country_revenue']
if 'country_ytd_revenue' in top_countries_df.columns:
    revenue_cols.append('country_ytd_revenue')

revenue_trend = top_countries_df.groupby(['revenue_month', 'country'])[revenue_cols].sum().reset_index()
country_trend = revenue_trend[revenue_trend['country'] == selected_country]

if 'country_revenue' in country_trend.columns:
    country_trend['prev_month'] = country_trend['country_revenue'].shift(1)
    country_trend['growth_pct'] = (country_trend['country_revenue'] - country_trend['prev_month']) / country_trend['prev_month']
    country_trend['hover_text'] = country_trend.apply(
        lambda x: f"{x['revenue_month']}: ${x['country_revenue']:,.0f}" + (f" ({x['growth_pct']*100:+.1f}%)" if x['prev_month'] else ""), axis=1
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=country_trend['revenue_month'],
        y=country_trend['country_revenue'],
        mode='lines+markers+text',
        text=country_trend['hover_text'],
        textposition="top center",
        name='Monthly Revenue',
        line=dict(color='blue')
    ))
    if 'country_ytd_revenue' in country_trend.columns:
        fig.add_trace(go.Scatter(
            x=country_trend['revenue_month'],
            y=country_trend['country_ytd_revenue'],
            mode='lines+markers',
            name='YTD Revenue',
            line=dict(color='green'),
            hovertemplate='%{x}: $%{y:,.0f}<extra></extra>'
        ))
    fig.update_layout(title=f"{selected_country} Revenue & YTD Trend", xaxis_title="Month", yaxis_title="Revenue")
    st.plotly_chart(fig, width='stretch')

# -----------------------------
# 8. Top Customers Table
# -----------------------------
st.subheader("Top Customers")
if 'top_customer_ltv' in country_df.columns:
    top_customers = country_df[['top_customer_id', 'top_customer_ltv', 'top_customer_contribution_pct','top_customer_yoy_growth_pct']].drop_duplicates()
    if not top_customers.empty:
        top_customers = top_customers.nlargest(5, 'top_customer_ltv')
        top_customers['label'] = top_customers.apply(
            lambda x: f"${x['top_customer_ltv']:,.0f}\n{x['top_customer_contribution_pct']*100:.1f}%" 
            if x['top_customer_contribution_pct'] else f"${x['top_customer_ltv']:,.0f}", axis=1)

        hover_cols = ['top_customer_id', 'top_customer_ltv']
        for col in ['top_customer_contribution_pct','top_customer_yoy_growth_pct']:
            if col in top_customers.columns:
                hover_cols.append(col)

        customer_chart = px.bar(
            top_customers,
            x='top_customer_id',
            y='top_customer_ltv',
            text='label',
            color='top_customer_ltv',
            hover_data=hover_cols
        )
        st.plotly_chart(customer_chart, width='stretch')

# -----------------------------
# 9. Global Genre Revenue Trend
# -----------------------------
st.subheader("Global Genre Revenue Trend")
if 'genre_revenue_global' in df.columns:
    genre_trend = df.groupby(['revenue_month', 'genre_name'])['genre_revenue_global'].sum().reset_index()
    selected_genre_trend = genre_trend[genre_trend['genre_name'] == selected_genre]
    fig_genre = px.line(
        selected_genre_trend,
        x='revenue_month',
        y='genre_revenue_global',
        hover_data=[c for c in ['revenue_month','genre_revenue_global'] if c in selected_genre_trend.columns],
        title=f"Global Revenue Trend for {selected_genre}"
    )
    st.plotly_chart(fig_genre, width='stretch')

# -----------------------------
# 10. Country vs Global Genre Comparison
# -----------------------------
st.subheader(f"{selected_genre} - Country vs Global Comparison")
if 'genre_revenue_country' in country_df.columns and 'genre_revenue_global' in df.columns:
    country_genre_trend = country_df[country_df['genre_name'] == selected_genre].groupby('revenue_month')['genre_revenue_country'].sum().reset_index()
    global_genre_trend = df[df['genre_name'] == selected_genre].groupby('revenue_month')['genre_revenue_global'].sum().reset_index()
    trend_merge = pd.merge(country_genre_trend, global_genre_trend, on='revenue_month', how='outer').fillna(0)

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Scatter(
        x=trend_merge['revenue_month'],
        y=trend_merge['genre_revenue_country'],
        mode='lines+markers',
        name=f"{selected_country} Revenue",
        line=dict(color='blue'),
        hovertemplate='%{x}: $%{y:,.0f}<extra></extra>'
    ))
    fig_cmp.add_trace(go.Scatter(
        x=trend_merge['revenue_month'],
        y=trend_merge['genre_revenue_global'],
        mode='lines+markers',
        name="Global Revenue",
        line=dict(color='orange'),
        hovertemplate='%{x}: $%{y:,.0f}<extra></extra>'
    ))
    fig_cmp.update_layout(
        title=f"{selected_genre} Revenue: {selected_country} vs Global",
        xaxis_title="Month",
        yaxis_title="Revenue",
        hovermode="x unified"
    )
    st.plotly_chart(fig_cmp, width='stretch')
