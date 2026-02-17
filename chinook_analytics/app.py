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
# 2. Connect to DuckDB via dbt (Cached)
# -----------------------------
@st.cache_resource
def get_connection():
    dbt_profiles_path = os.path.expanduser("~/.dbt/profiles.yml")
    with open(dbt_profiles_path) as f:
        profiles = yaml.safe_load(f)

    profile_name = list(profiles.keys())[0]
    target_name = profiles[profile_name]['target']
    duckdb_path = profiles[profile_name]['outputs'][target_name]['path']

    return duckdb.connect(duckdb_path)

conn = get_connection()

# -----------------------------
# 3. Refresh dbt & Load Data
# -----------------------------
@st.cache_data
def load_data():
    return conn.execute("SELECT * FROM fct_music_kpi").df()

def run_dbt_and_reload():
    try:
        st.info("Running dbt models...")
        subprocess.run(
            ["dbt", "run"],
            check=True,
            cwd="C:/kev/chinook_music/chinook/chinook_analytics"
        )
        st.success("dbt run completed. Reloading fresh data...")
        load_data.clear()
        return load_data()
    except subprocess.CalledProcessError as e:
        st.error("dbt run failed. Check terminal for details.")
        st.stop()

if st.button("🔄 Refresh Data (Run dbt)"):
    df = run_dbt_and_reload()
else:
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
# 5. KPI Cards (Auto-Hide Empty)
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

country_revenue = country_df['country_revenue'].sum() if 'country_revenue' in country_df.columns else None
top_genre_revenue = country_df['genre_revenue_country'].max() if 'genre_revenue_country' in country_df.columns else None
top_ltv = country_df['top_customer_ltv'].max() if 'top_customer_ltv' in country_df.columns else None
top_contrib = country_df['top_customer_contribution_pct'].max() if 'top_customer_contribution_pct' in country_df.columns else None
yoy = country_df['country_yoy_growth_pct'].mean() if 'country_yoy_growth_pct' in country_df.columns else None

cols = st.columns(5)
cols[0].metric("Country Revenue", f"${country_revenue:,.0f}" if country_revenue else "N/A")
cols[1].metric("Top Genre Revenue", f"${top_genre_revenue:,.0f}" if top_genre_revenue else "N/A")
cols[2].metric("Top Customer LTV", f"${top_ltv:,.0f}" if top_ltv else "N/A")
cols[3].metric("Top Customer Contribution", f"{top_contrib*100:.2f}%" if top_contrib else "N/A")
yoy_text, yoy_color = growth_metric(yoy)
cols[4].metric("Country YoY Growth", yoy_text, delta_color=yoy_color)

# -----------------------------
# 5B. Executive Summary
# -----------------------------
st.subheader("📊 Executive Summary")
summary_lines = []
if country_revenue:
    summary_lines.append(f"{selected_country} generated ${country_revenue:,.0f} in total revenue.")
if top_genre_revenue:
    top_genre_name = country_df.sort_values("genre_revenue_country", ascending=False).iloc[0]["genre_name"]
    summary_lines.append(f"{top_genre_name} is the top-performing genre with ${top_genre_revenue:,.0f} in revenue.")
if summary_lines:
    st.markdown(" ".join(summary_lines))

# -----------------------------
# 6. Top Genres per Country Chart with K/M Hover & Conditional Coloring
# -----------------------------
st.subheader("Top Genres per Country (Top 5)")

if 'genre_revenue_country' in country_df.columns:
    top_genres = country_df.sort_values("genre_revenue_country", ascending=False).drop_duplicates("genre_name").head(5)
    top_genres["display_name"] = top_genres["genre_name"]
    
    # Conditional coloring
    top_genres["color"] = top_genres["genre_revenue_country"].apply(lambda x: "green" if x >= top_genre_revenue*0.6 else "orange")
    
    # K/M formatting
    def km_format(x):
        if x >= 1_000_000:
            return f"${x/1_000_000:.1f}M"
        elif x >= 1_000:
            return f"${x/1_000:.1f}K"
        return f"${x:.0f}"
    
    top_genres["hover_revenue"] = top_genres["genre_revenue_country"].apply(km_format)
    
    genre_chart = px.bar(
        top_genres,
        x="display_name",
        y="genre_revenue_country",
        color="color",
        text="hover_revenue",
        hover_data=["genre_name", "genre_revenue_country"]
    )
    genre_chart.update_layout(showlegend=False)
    st.plotly_chart(genre_chart, width='stretch')

# -----------------------------
# 6B. Optional CSV Download Button
# -----------------------------
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=country_df.to_csv(index=False),
    file_name=f"{selected_country}_data.csv",
    mime="text/csv"
)
