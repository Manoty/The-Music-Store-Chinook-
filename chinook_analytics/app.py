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
st.markdown(
    "Interactive revenue intelligence platform powered by dbt and Streamlit, delivering country performance insights, customer value analytics, and genre trend monitoring with real-time refresh capability."
)

# -----------------------------
# 2. Connect to DuckDB via dbt (Cached)
@st.cache_resource
def get_connection():
    db_path = os.path.join(os.path.dirname(__file__), "dev.duckdb")

    if not os.path.exists(db_path):
        st.error(f"DuckDB file not found at {db_path}")
        st.stop()

    return duckdb.connect(db_path)
# -----------------------------
# 3. Refresh dbt & Load Data
# -----------------------------
@st.cache_data
@st.cache_data
def load_data():
    conn = get_connection()
    return conn.execute("SELECT * FROM fct_music_kpi").df()

def run_dbt_and_reload():
    try:
        st.info("Running dbt models...")

        subprocess.run(
            ["dbt", "run"],
            check=True,
            cwd="C:/kev/chinook_music/chinook/chinook_analytics"  # 👈 dbt project root
        )

        st.success("dbt run completed. Reloading fresh data...")
        load_data.clear()
        return load_data()

    except subprocess.CalledProcessError:
        st.error("dbt run failed. Check terminal for details.")
        st.stop()

if st.button("🔄 Refresh Data (Run dbt)"):
    df = run_dbt_and_reload()
else:
    df = load_data()

# -----------------------------
# Optional: Debug panel to see columns
# -----------------------------
st.sidebar.subheader("Debug: Available Columns")
st.sidebar.write(df.columns.tolist())

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
# 5. KPI Cards (Auto-Hide Empty + K/M formatting)
# -----------------------------
st.subheader(f"Top KPIs for {selected_country}")

def format_currency(val):
    """Format number with K / M suffix"""
    if val >= 1_000_000:
        return f"${val/1_000_000:,.1f}M"
    elif val >= 1_000:
        return f"${val/1_000:,.1f}K"
    else:
        return f"${val:,.0f}"

country_revenue = country_df['country_revenue'].sum() if 'country_revenue' in country_df.columns else None
top_genre_revenue = country_df['genre_revenue_country'].max() if 'genre_revenue_country' in country_df.columns else None
top_ltv = country_df['top_customer_ltv'].max() if 'top_customer_ltv' in country_df.columns else None
top_contrib = country_df['top_customer_contribution_pct'].max() if 'top_customer_contribution_pct' in country_df.columns else None
yoy = country_df['country_yoy_growth_pct'].mean() if 'country_yoy_growth_pct' in country_df.columns else None

kpis = []

if country_revenue and country_revenue > 0:
    kpis.append({
        "label": "Country Revenue",
        "value": format_currency(country_revenue),
        "delta": "Healthy",
        "color": "normal"
    })

if top_genre_revenue and top_genre_revenue > 0:
    kpis.append({
        "label": "Top Genre Revenue",
        "value": format_currency(top_genre_revenue),
        "delta": "Strong",
        "color": "normal"
    })

if top_ltv and top_ltv > 0:
    kpis.append({
        "label": "Top Customer LTV",
        "value": format_currency(top_ltv),
        "delta": "High Value",
        "color": "normal"
    })

if top_contrib and top_contrib > 0:
    kpis.append({
        "label": "Top Customer Contribution",
        "value": f"{top_contrib*100:.2f}%",
        "delta": "Dominant" if top_contrib > 0.20 else "Low",
        "color": "normal" if top_contrib > 0.20 else "inverse"
    })

if yoy is not None:
    kpis.append({
        "label": "Country YoY Growth",
        "value": f"{yoy*100:.2f}%",
        "delta": f"{yoy*100:.2f}%",
        "color": "normal" if yoy > 0 else "inverse"
    })

if kpis:
    cols = st.columns(len(kpis))
    for col, kpi in zip(cols, kpis):
        col.metric(
            kpi["label"],
            kpi["value"],
            delta=kpi["delta"],
            delta_color=kpi["color"]
        )
else:
    st.info("No KPI data available for this country.")

# -----------------------------
# 5B. Executive Summary
# -----------------------------
st.subheader("📊 Executive Summary")

summary_lines = []

if country_revenue and country_revenue > 0:
    summary_lines.append(f"{selected_country} generated {format_currency(country_revenue)} million dollars in total revenue.")

if yoy is not None:
    if yoy > 0:
        summary_lines.append(f"Revenue is growing at {yoy*100:.2f}% year-over-year, indicating positive momentum.")
    elif yoy < 0:
        summary_lines.append(f"Revenue declined by {abs(yoy*100):.2f}% year-over-year, signaling potential market pressure.")

if top_genre_revenue and top_genre_revenue > 0:
    top_genre_name = (
        country_df.sort_values("genre_revenue_country", ascending=False)
        .iloc[0]["genre_name"] if "genre_name" in country_df.columns else "the leading genre"
    )
    summary_lines.append(f"{top_genre_name} is the top-performing genre with {format_currency(top_genre_revenue)} million dollars in revenue.")

if top_contrib and top_contrib > 0:
    if top_contrib > 0.25:
        summary_lines.append(f"Top customer contribution is {top_contrib*100:.2f}%, indicating revenue concentration risk.")
    else:
        summary_lines.append(f"Top customer contribution stands at {top_contrib*100:.2f}%, showing diversified revenue distribution.")

if summary_lines:
    st.markdown(" ".join(summary_lines))
else:
    st.info("Not enough data available to generate executive summary.")

# -----------------------------
# The rest of your app (charts, top customers, global genre trend, comparison) remains unchanged
# -----------------------------
# You can keep the rest of your working code for:
# - Top Genres per Country
# - Country Revenue Trend
# - Top Customers
# - Global Genre Revenue Trend
# - Country vs Global Comparison
# without modification.




## -----------------------------
# -----------------------------
# 6. Top Genres per Country Chart
# -----------------------------
st.subheader("Top Genres per Country (Top 5)")

st.markdown("""
This chart ranks the top N countries based on total revenue performance. 
It helps identify which geographic markets contribute the most to overall business revenue.
""")


if 'genre_revenue_country' in country_df.columns:

    top_genres = (
        country_df
        .sort_values("genre_revenue_country", ascending=False)
        .drop_duplicates(subset=["genre_name"])
        .head(5)
        .copy()
    )

    # Add ranking
    top_genres["rank"] = range(1, len(top_genres) + 1)

    # Medal column
    medal_map = {
        1: "🥇",
        2: "🥈",
        3: "🥉"
    }

    top_genres["medal"] = top_genres["rank"].map(medal_map).fillna("")

    # Display label with medal
    top_genres["display_name"] = top_genres["medal"] + " " + top_genres["genre_name"]

    # Market share label
    if 'genre_market_share_pct' in top_genres.columns:
        top_genres["market_share_label"] = (
            (top_genres["genre_market_share_pct"] * 100)
            .round(1)
            .astype(str) + "%"
        )
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
        x="display_name",
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

st.markdown("""
This chart displays the monthly revenue performance for the selected country, along with optional year-to-date (YTD) revenue trends. 
It highlights short-term growth patterns, month-over-month changes, and cumulative performance over time.
""")


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

st.markdown("""
This chart shows the percentage of total revenue contributed by the top customers. 
It helps assess revenue dependency and determine whether sales are diversified or concentrated among a few clients.)
""")
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

st.markdown("""
This chart visualizes monthly global revenue trends across all music genres. 
It provides a macro-level perspective on international demand and industry performance shifts.
""")

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

st.markdown("""
This chart compares the selected country’s genre performance against global revenue trends for the same genre. 
It helps determine whether the country is outperforming or underperforming the broader global market.
""")

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



# 🔹 1️⃣ Top 10 Genres by Revenue
st.subheader("🎸 Top 10 Genres by Revenue")

st.markdown("""
This chart ranks the top-performing genres within the selected country by total revenue. 
It provides insight into consumer preferences and highlights key revenue-driving categories.
""")

source_df = country_df if "country_df" in locals() else df

if {"genre_name", "genre_revenue_country"}.issubset(source_df.columns):
    
    top_genres = (
        source_df.loc[:, ["genre_name", "genre_revenue_country"]]
        .dropna()
        .groupby("genre_name", as_index=False)
        .agg({"genre_revenue_country": "sum"})
        .sort_values("genre_revenue_country", ascending=False)
        .head(10)
        .copy()
    )
    
    if not top_genres.empty:
        fig = px.bar(
            top_genres,
            x="genre_revenue_country",
            y="genre_name",
            orientation="h",
            title="Top 10 Genres by Revenue"
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No genre revenue data available for this selection.")
else:
    st.warning("Required genre columns not found in dataset.")

st.subheader("🌎 Revenue by Country (Top N)")

st.markdown("""
This chart ranks the top N countries based on total revenue performance. 
It helps identify which geographic markets contribute the most to overall business revenue.
""")

if {"country", "country_revenue"}.issubset(df.columns):

    top_countries = (
        df.groupby("country", as_index=False)["country_revenue"].sum()
        .sort_values("country_revenue", ascending=False)
        .head(top_n_countries)
        .copy()
    )

    if not top_countries.empty:
        fig = px.bar(
            top_countries,
            x="country_revenue",
            y="country",
            orientation="h",
            title=f"Top {top_n_countries} Countries by Revenue",
            text=top_countries["country_revenue"].apply(lambda x: f"${x:,.0f}")
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No country revenue data available.")
else:
    st.warning("Required country columns not found in dataset.")


st.subheader("📊 Global Genre Revenue Trend")

st.markdown("""
This chart visualizes monthly global revenue trends across all music genres.
It provides a macro-level perspective on international demand and industry performance shifts.
""")


if {"revenue_month", "genre_name", "genre_revenue_global"}.issubset(df.columns):

    genre_trend_df = (
        df.groupby(["revenue_month", "genre_name"], as_index=False)["genre_revenue_global"].sum()
        .copy()
    )

    if not genre_trend_df.empty:
        fig = px.line(
            genre_trend_df,
            x="revenue_month",
            y="genre_revenue_global",
            color="genre_name",
            title="Global Genre Revenue Trend",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No global genre revenue data available.")
else:
    st.warning("Required global genre columns not found.")


st.subheader("💾 Download Data")

st.markdown("""
This feature allows users to download the full KPI dataset in CSV format for further analysis. 
It supports reporting, advanced modeling, and executive sharing outside the dashboard environment.
""")


if not df.empty:
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Full Dataset",
        data=csv,
        file_name="music_dashboard_data.csv",
        mime="text/csv"
    )
else:
    st.info("No data available to download.")
