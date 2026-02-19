{{ config(materialized='table') }}

SELECT
    CURRENT_TIMESTAMP AS validation_run_time,
    COUNT(*) AS total_rows,
    SUM(CASE WHEN country_revenue IS NULL THEN 1 ELSE 0 END) AS null_revenue_count,
    SUM(CASE WHEN country_yoy_growth_pct IS NULL THEN 1 ELSE 0 END) AS null_growth_count,
    
FROM {{ ref('fct_music_kpi') }}
