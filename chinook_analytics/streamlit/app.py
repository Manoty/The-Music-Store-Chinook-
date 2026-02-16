import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# -----------------------------
# 1. Connect to your dbt output (DuckDB)
# -----------------------------
st.set_page_config(page_title="Music Store KPI Dashboard", layout="wide")
st.title("🎵 Music Store KPI Dashboard")

conn = duckdb.connect("chinook_analytics.duckdb")

# -----------------------------
# 2. Load KPI Mart
# -----------------------------
@st.cache_data
def load_data():
    return conn.execute("SELECT * FROM fct_music_kpi").df()

df = load_data()

# -----------------------------
# 3. Sidebar filters
# -----------------------------
st.sidebar.header("Filters")
top_n_countries = st.sidebar.slider("Top N countries", min_value=1, max_value=10, value=5)
selected_country = st.sidebar.selectbox("Select Country", options=df['country'].unique())
selected_genre = st.sidebar.selectbox("Select Genre", options=df['genre_name'].unique())

# Filter Top N countries
top_countries_df = df[df['country_rank'] <= top_n_countries]

# Filter for selected country
country_df = top_countries_df[top_countries_df['country'] == selected_country]

# -----------------------------
# 4. KPI Cards
# -----------------------------
st.subheader(f"Top KPIs for {selected_country}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Country Revenue", f"${country_df['country_revenue'].sum():,.0f}")
col2.metric("Top Genre Revenue", f"${country_df['genre_revenue_country'].max():,.0f}")
col3.metric("Top Customer LTV", f"${country_df['top_customer_ltv'].max():,.0f}")
col4.metric("Top Customer Contribution", f"{(country_df['top_customer_contribution_pct'].max()*100):.2f}%")

# -----------------------------
# 5. Charts
# -----------------------------

# 5a. Top genres per country (Bar)
st.subheader("Top Genres per Country (Top 5)")
genre_chart = px.bar(
    country_df,
    x="genre_name",
    y="genre_revenue_country",
    text="genre_market_share_pct",
    color="genre_name",
    labels={"genre_revenue_country": "Revenue", "genre_name": "Genre"},
)
st.plotly_chart(genre_chart, use_container_width=True)

# 5b. Country revenue trend (Line)
st.subheader("Country Revenue Trend")
revenue_trend = top_countries_df.groupby(['revenue_month', 'country'])['country_revenue'].sum().reset_index()
trend_chart = px.line(
    revenue_trend[revenue_trend['country']==selected_country],
    x="revenue_month",
    y="country_revenue",
    title=f"Revenue Trend: {selected_country}"
)
st.plotly_chart(trend_chart, use_container_width=True)

# 5c. Top Customers (Bar)
st.subheader("Top Customers")
top_customers = country_df[['top_customer_id', 'top_customer_ltv']].drop_duplicates().nlargest(5, 'top_customer_ltv')
customer_chart = px.bar(top_customers, x='top_customer_id', y='top_customer_ltv', text='top_customer_ltv')
st.plotly_chart(customer_chart, use_container_width=True)

# 5d. Global Genre Trend (Line)
st.subheader("Global Genre Revenue Trend")
genre_trend = df.groupby(['revenue_month', 'genre_name'])['genre_revenue_global'].sum().reset_index()
genre_line = px.line(
    genre_trend[genre_trend['genre_name']==selected_genre],
    x='revenue_month',
    y='genre_revenue_global',
    title=f"Global Trend for {selected_genre}"
)
st.plotly_chart(genre_line, use_container_width=True)
