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
selected_country = st.sidebar.selectbox("Select Country", df['Country'].unique())
selected_genre = st.sidebar.selectbox("Select Genre", df['genre_name'].unique())

top_countries_df = df.head(top_n_countries)
country_df = df[df['Country'] == selected_country]

# -----------------------------
# 5. KPI Cards (Updated safely)
# -----------------------------
st.subheader(f"Top KPIs for {selected_country}")

def growth_metric(val):
    if val is None:
        return "N/A", "gray"
    elif val > 0:
        return f"{val*100:.2f}% ↑", "green"
    elif val < 0:
        return f"{val*100:.2f}% ↓", "red"
    else:
        return "0%", "gray"

# Safe defaults for KPIs
country_revenue = country_df['country_revenue'].sum() if 'country_revenue' in country_df.columns else 0
top_genre_revenue = country_df['genre_revenue_country'].max() if 'genre_revenue_country' in country_df.columns else 0
top_ltv = country_df['top_customer_ltv'].max() if 'top_customer_ltv' in country_df.columns else 0
top_contrib = country_df['top_customer_contribution_pct'].max() if 'top_customer_contribution_pct' in country_df.columns else 0
yoy = country_df['country_yoy_growth_pct'].mean() if 'country_yoy_growth_pct' in country_df.columns else 0

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Country Revenue", f"${country_revenue:,.0f}")
col2.metric("Top Genre Revenue", f"${top_genre_revenue:,.0f}")
col3.metric("Top Customer LTV", f"${top_ltv:,.0f}")
col4.metric("Top Customer Contribution", f"{top_contrib*100:.2f}%")
yoy_text, yoy_color = growth_metric(yoy)
col5.metric("Country YoY Growth", yoy_text, delta_color=yoy_color)

# -----------------------------
# 6. Top Genres Bar Chart
# -----------------------------
genre_chart = px.bar(
    country_df.sort_values('genre_revenue_country', ascending=False).head(10),
    x='genre_name',
    y='genre_revenue_country',
    color='genre_revenue_country',
    hover_data={
        'genre_revenue_country': True,
        'genre_market_share_pct': True,
        'genre_market_share_rank': True,
        'genre_revenue_global': True,
        'genre_rank_global': True
    },
    labels={
        'genre_name': 'Genre',
        'genre_revenue_country': 'Revenue'
    },
    title=f"Top Genres in {selected_country}"
)
st.plotly_chart(genre_chart, use_container_width=True)

# -----------------------------
# 7. Country Revenue Trend Line Chart
# -----------------------------
if 'revenue_month' in country_df.columns:
    revenue_trend = country_df.groupby(['revenue_month', 'Country'])[['country_revenue']].sum().reset_index()
    revenue_chart = px.line(
        revenue_trend,
        x='revenue_month',
        y='country_revenue',
        color='Country',
        markers=True,
        title=f"{selected_country} Revenue Trend"
    )
    st.plotly_chart(revenue_chart, use_container_width=True)

# -----------------------------
# 8. Top Customers Table
# -----------------------------
if 'top_customer_ltv' in country_df.columns:
    top_customers_table = country_df[['top_customer_id', 'top_customer_ltv', 'top_customer_contribution_pct']].sort_values(
        'top_customer_ltv', ascending=False
    ).head(10)
    top_customers_table['top_customer_contribution_pct'] = (top_customers_table['top_customer_contribution_pct']*100).round(2)
    st.subheader("Top Customers")
    st.dataframe(top_customers_table)

# -----------------------------
# 9. Global vs Country Genre Revenue Comparison
# -----------------------------
if 'genre_revenue_global' in country_df.columns:
    genre_comparison = px.bar(
        country_df.sort_values('genre_revenue_country', ascending=False).head(10),
        x='genre_name',
        y=['genre_revenue_country', 'genre_revenue_global'],
        barmode='group',
        labels={
            'value': 'Revenue',
            'variable': 'Scope'
        },
        title=f"{selected_genre} - Country vs Global Comparison"
    )
    st.plotly_chart(genre_comparison, use_container_width=True)
