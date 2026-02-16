import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# 1. Streamlit Page Setup
# -----------------------------
st.set_page_config(page_title="Music Store Executive Dashboard", layout="wide")
st.title("🎵 Music Store Executive Dashboard")
st.markdown("Interactive KPIs, trends, and top customers by country & genre")

conn = duckdb.connect("chinook_analytics.duckdb")

# -----------------------------
# 2. Load KPI Mart
# -----------------------------
@st.cache_data
def load_data():
    return conn.execute("SELECT * FROM fct_music_kpi").df()

df = load_data()

# -----------------------------
# 3. Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")
top_n_countries = st.sidebar.slider("Top N countries", min_value=1, max_value=10, value=5)
selected_country = st.sidebar.selectbox("Select Country", options=df['country'].unique())
selected_genre = st.sidebar.selectbox("Select Genre", options=df['genre_name'].unique())

# Filter top countries
top_countries_df = df[df['country_rank'] <= top_n_countries]

# Filter for selected country
country_df = top_countries_df[top_countries_df['country'] == selected_country]

# -----------------------------
# 4. KPI Cards with Conditional Formatting
# -----------------------------
st.subheader(f"Top KPIs for {selected_country}")

def format_growth(val):
    if val is None:
        return "N/A"
    return f"{val*100:.2f}% 🔼" if val > 0 else f"{val*100:.2f}% 🔽"

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Country Revenue", f"${country_df['country_revenue'].sum():,.0f}")
col2.metric("Top Genre Revenue", f"${country_df['genre_revenue_country'].max():,.0f}")
col3.metric("Top Customer LTV", f"${country_df['top_customer_ltv'].max():,.0f}")
col4.metric("Top Customer Contribution", f"{(country_df['top_customer_contribution_pct'].max()*100):.2f}%")
col5.metric("Country YoY Growth", format_growth(country_df['country_yoy_growth_pct'].mean()))

# -----------------------------
# 5. Charts
# -----------------------------

# 5a. Top genres per country (Bar)
st.subheader("Top Genres per Country (Top 5)")
genre_chart = px.bar(
    country_df,
    x="genre_name",
    y="genre_revenue_country",
    text=country_df['genre_market_share_pct'].apply(lambda x: f"{x*100:.1f}%"),
    color="genre_name",
    labels={"genre_revenue_country": "Revenue", "genre_name": "Genre"},
)
genre_chart.update_layout(showlegend=False)
st.plotly_chart(genre_chart, use_container_width=True)

# 5b. Country Revenue Trend (Line + YTD shading)
st.subheader("Country Revenue Trend")
revenue_trend = top_countries_df.groupby(['revenue_month', 'country'])[['country_revenue', 'country_ytd_revenue']].sum().reset_index()
country_trend = revenue_trend[revenue_trend['country'] == selected_country]
fig = go.Figure()
fig.add_trace(go.Scatter(x=country_trend['revenue_month'], y=country_trend['country_revenue'],
                         mode='lines+markers', name='Monthly Revenue', line=dict(color='blue')))
fig.add_trace(go.Scatter(x=country_trend['revenue_month'], y=country_trend['country_ytd_revenue'],
                         mode='lines+markers', name='YTD Revenue', line=dict(color='green')))
fig.update_layout(title=f"{selected_country} Revenue & YTD Trend", xaxis_title="Month", yaxis_title="Revenue")
st.plotly_chart(fig, use_container_width=True)

# 5c. Top Customers (Bar with contribution %)
st.subheader("Top Customers")
top_customers = country_df[['top_customer_id', 'top_customer_ltv', 'top_customer_contribution_pct']].drop_duplicates().nlargest(5, 'top_customer_ltv')
top_customers['label'] = top_customers.apply(lambda x: f"${x['top_customer_ltv']:,.0f}\n{x['top_customer_contribution_pct']*100:.1f}%", axis=1)
customer_chart = px.bar(top_customers, x='top_customer_id', y='top_customer_ltv', text='label', color='top_customer_ltv')
st.plotly_chart(customer_chart, use_container_width=True)

# 5d. Global Genre Revenue Trend (Line)
st.subheader("Global Genre Revenue Trend")
genre_trend = df.groupby(['revenue_month', 'genre_name'])['genre_revenue_global'].sum().reset_index()
selected_genre_trend = genre_trend[genre_trend['genre_name'] == selected_genre]
fig_genre = px.line(selected_genre_trend, x='revenue_month', y='genre_revenue_global',
                    title=f"Global Revenue Trend for {selected_genre}")
st.plotly_chart(fig_genre, use_container_width=True)
