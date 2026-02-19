{{ config(materialized='table') }}

WITH revenue_stats AS (

    SELECT
        country,
        country_revenue,
        country_yoy_growth_pct,

        AVG(country_revenue) OVER() AS avg_revenue,
        STDDEV(country_revenue) OVER() AS std_revenue

    FROM {{ ref('fct_music_kpi') }}

)

SELECT
    country,
    country_revenue,
    country_yoy_growth_pct,

    CASE
        WHEN country_revenue > avg_revenue + (2 * std_revenue)
        THEN 'High Revenue Anomaly'

        WHEN country_revenue < avg_revenue - (2 * std_revenue)
        THEN 'Low Revenue Anomaly'

        ELSE 'Normal'
    END AS revenue_anomaly_flag,

    CASE
        WHEN country_yoy_growth_pct > 1
        THEN 'Extreme Growth'

        WHEN country_yoy_growth_pct < -0.5
        THEN 'Severe Decline'

        ELSE 'Normal'
    END AS growth_anomaly_flag

FROM revenue_stats
