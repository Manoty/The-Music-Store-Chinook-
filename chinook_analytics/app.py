import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import subprocess

st.set_page_config(page_title="Music Store Executive Dashboard", layout="wide")

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.big-font {
    font-size:18px !important;
}
.section-spacing {
    margin-top: 30px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Currency Formatter (Auto Scale)
# -----------------------------
def format_currency(value):
    if value is None:
        return "N/A"
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    elif value >= 1_000:
        return f"${value/1_000:.1f}K"
    else:
        return f"${value:,.0f}"

# -----------------------------
# Load Data
# -----------------------------
@st.cache_data
def load_data():
    con = duckdb.connect("dev.duckdb")
    df = con.execute("SELECT * FROM fct_music_kpi").df()
    return df

# -----------------------------
# Safe dbt Run
# -----------------------------
def run_dbt_and_reload():
    try:
        subprocess.run(["dbt", "run"], check=True)
        st.success("dbt models refreshed successfully.")
    except subprocess.CalledProcessError:
        st.error("dbt run failed. Check terminal for detailed error.")
    return load_data()

# -----------------------------
# Header
# -----------------------------
st.title("🎵 Music Store Executive Dashboard")
st.caption("Interactive KPIs, trends, top customers, with executive visuals & one-click dbt refresh")

if st.button("🔄 Refresh Data (Run dbt)"):
    st.info("Running dbt models...")
    df = run_dbt_and_reload()
else:
    df = load_data()

# Ensure pandas DataFrame (fix narwhals issues)
df = pd.DataFrame(df)

# -----------------------------
# Sidebar Filters
# -----------------------------
st.sidebar.header("Filters")

top_n = st.sidebar.slider("Top N countries", 1, 10, 5)

countries = df["country"].dropna().unique()
selected_country = st.sidebar.selectbox("Select Country", sorted(countries))

genres = df["genre_name"].dropna().unique()
selected_genre = st.sidebar.selectbox("Select Genre", sorted(genres))

# -----------------------------
# Filtered Data
# -----------------------------
country_df = df[df["country"] == selected_country].copy()

# -----------------------------
# KPIs
# -----------------------------
st.subheader(f"Top KPIs for {selected_country}")

country_revenue = country_df["country_revenue"].max()

top_genre_revenue = (
    country_df.groupby("genre_name")["genre_revenue_country"]
    .max()
    .max()
)

top_customer_df = (
    country_df.groupby("customer_name")["customer_ltv"]
    .max()
    .reset_index()
)

top_ltv = top_customer_df["customer_ltv"].max() if not top_customer_df.empty else None

top_contrib = (
    country_df["top_customer_pct"]
    .max()
    if "top_customer_pct" in country_df.columns
    else None
)

yoy = (
    country_df["yoy_growth"]
    .max()
    if "yoy_growth" in country_df.columns
    else None
)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Country Revenue", format_currency(country_revenue))

with col2:
    st.metric("Top Genre Revenue", format_currency(top_genre_revenue))

with col3:
    st.metric("Top Customer LTV", format_currency(top_ltv))

with col4:
    if top_contrib:
        st.metric("Top Customer Contribution", f"{top_contrib*100:.2f}%")
    else:
        st.metric("Top Customer Contribution", "N/A")

with col5:
    if yoy:
        st.metric("Country YoY Growth", f"{yoy*100:.2f}%")
    else:
        st.metric("Country YoY Growth", "N/A")

# -----------------------------
# Executive Summary
# -----------------------------
st.markdown("---")
st.subheader("📊 Executive Summary")

summary_lines = []

if country_revenue and country_revenue > 0:
    summary_lines.append(
        f"{selected_country} generated {format_currency(country_revenue)} in total revenue."
    )

if yoy is not None:
    if yoy > 0:
        summary_lines.append(
            f"Revenue is growing at {yoy*100:.2f}% year-over-year, indicating positive momentum."
        )
    elif yoy < 0:
        summary_lines.append(
            f"Revenue declined by {abs(yoy*100):.2f}% year-over-year."
        )

if top_genre_revenue and top_genre_revenue > 0:
    top_genre_name = (
        country_df.groupby("genre_name")["genre_revenue_country"]
        .max()
        .sort_values(ascending=False)
        .index[0]
    )
    summary_lines.append(
        f"{top_genre_name} is the top-performing genre with {format_currency(top_genre_revenue)} in revenue."
    )

if top_contrib and top_contrib > 0:
    if top_contrib > 0.25:
        summary_lines.append(
            f"Top customer contribution is {top_contrib*100:.2f}%, indicating revenue concentration risk."
        )
    else:
        summary_lines.append(
            f"Top customer contribution stands at {top_contrib*100:.2f}%, showing diversified revenue distribution."
        )

if summary_lines:
    st.markdown(
        f"""
        <div class="big-font">
        {' '.join(summary_lines)}
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.info("Not enough data available to generate executive summary.")

# -----------------------------
# Top Genres (Bar Chart)
# -----------------------------
st.markdown("---")
st.subheader("Top Genres per Country (Top 5)")

top_genres = (
    country_df.groupby("genre_name")["genre_revenue_country"]
    .max()
    .reset_index()
    .sort_values(by="genre_revenue_country", ascending=False)
    .head(5)
)

fig_genre = px.bar(
    top_genres,
    x="genre_name",
    y="genre_revenue_country",
    title="Top 5 Genres"
)

st.plotly_chart(fig_genre, use_container_width=True)

# -----------------------------
# Country Revenue Trend
# -----------------------------
if "year" in country_df.columns:
    st.markdown("---")
    st.subheader("Country Revenue Trend")

    yearly = (
        country_df.groupby("year")["country_revenue"]
        .max()
        .reset_index()
        .sort_values("year")
    )

    fig_trend = px.line(yearly, x="year", y="country_revenue")
    st.plotly_chart(fig_trend, use_container_width=True)

# -----------------------------
# Top Customers
# -----------------------------
st.markdown("---")
st.subheader("Top Customers")

top_customers = (
    country_df.groupby("customer_name")["customer_ltv"]
    .max()
    .reset_index()
    .sort_values(by="customer_ltv", ascending=False)
    .head(10)
)

fig_customers = px.bar(
    top_customers,
    x="customer_name",
    y="customer_ltv",
    title="Top 10 Customers by LTV"
)

st.plotly_chart(fig_customers, use_container_width=True)

# -----------------------------
# Global Genre Trend
# -----------------------------
st.markdown("---")
st.subheader("Global Genre Revenue Trend")

genre_df = df[df["genre_name"] == selected_genre]

if "year" in genre_df.columns:
    global_trend = (
        genre_df.groupby("year")["genre_revenue_global"]
        .max()
        .reset_index()
    )

    fig_global = px.line(global_trend, x="year", y="genre_revenue_global")
    st.plotly_chart(fig_global, use_container_width=True)

# -----------------------------
# Country vs Global Comparison
# -----------------------------
st.markdown("---")
st.subheader(f"{selected_genre} - Country vs Global Comparison")

if "genre_revenue_global" in country_df.columns:
    comparison_df = country_df[
        country_df["genre_name"] == selected_genre
    ][["genre_revenue_country", "genre_revenue_global"]].drop_duplicates()

    if not comparison_df.empty:
        comp = comparison_df.iloc[0]

        comp_df = pd.DataFrame({
            "Scope": ["Country", "Global"],
            "Revenue": [
                comp["genre_revenue_country"],
                comp["genre_revenue_global"]
            ]
        })

        fig_comp = px.bar(comp_df, x="Scope", y="Revenue")
        st.plotly_chart(fig_comp, use_container_width=True)
