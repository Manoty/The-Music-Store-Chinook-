# -----------------------------
# Country Revenue Trend
# -----------------------------
st.subheader("Country Revenue Trend")

# Safe check for YTD column
revenue_columns = ['country_revenue']
if 'country_ytd_revenue' in top_countries_df.columns:
    revenue_columns.append('country_ytd_revenue')

revenue_trend = top_countries_df.groupby(['revenue_month', 'country'])[revenue_columns].sum().reset_index()
country_trend = revenue_trend[revenue_trend['country'] == selected_country]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=country_trend['revenue_month'],
    y=country_trend['country_revenue'],
    mode='lines+markers',
    name='Monthly Revenue',
    line=dict(color='blue')
))
if 'country_ytd_revenue' in country_trend.columns:
    fig.add_trace(go.Scatter(
        x=country_trend['revenue_month'],
        y=country_trend['country_ytd_revenue'],
        mode='lines+markers',
        name='YTD Revenue',
        line=dict(color='green')
    ))
fig.update_layout(
    title=f"{selected_country} Revenue & YTD Trend",
    xaxis_title="Month",
    yaxis_title="Revenue"
)
st.plotly_chart(fig, width='stretch')
