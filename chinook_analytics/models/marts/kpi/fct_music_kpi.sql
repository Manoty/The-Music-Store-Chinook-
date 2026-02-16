with genre_country as (
    select *
    from {{ ref('fct_genre_country_month') }}
),

-- Top countries by monthly revenue
country_kpi as (
    select
        revenue_month,
        country,
        sum(total_revenue) as country_revenue,
        rank() over (partition by revenue_month order by sum(total_revenue) desc) as country_rank,
        lag(sum(total_revenue)) over (partition by country order by revenue_month) as prev_country_revenue
    from genre_country
    group by revenue_month, country
),

-- Top genres per month globally
genre_kpi as (
    select
        revenue_month,
        genre_name,
        sum(total_revenue) as genre_revenue_global,
        rank() over (partition by revenue_month order by sum(total_revenue) desc) as genre_rank_global,
        lag(sum(total_revenue)) over (partition by genre_name order by revenue_month) as prev_genre_revenue_global
    from genre_country
    group by revenue_month, genre_name
),

-- Top genres per country
genre_country_kpi as (
    select
        revenue_month,
        country,
        genre_name,
        total_revenue as genre_revenue_country,
        genre_market_share_pct,
        genre_market_share_rank
    from genre_country
    where genre_market_share_rank <= 5   -- Top 5 genres per country
)

select
    gc.revenue_month,
    gc.country,
    gc.genre_name,

    -- Country-level KPIs
    ck.country_revenue,
    ck.country_rank,
    ck.prev_country_revenue,
    case 
        when ck.prev_country_revenue is null or ck.prev_country_revenue = 0 then null
        else (ck.country_revenue - ck.prev_country_revenue) / ck.prev_country_revenue
    end as country_revenue_growth_pct,

    -- Genre in country KPIs
    gc.genre_revenue_country,
    gc.genre_market_share_pct,
    gc.genre_market_share_rank,

    -- Global genre KPIs
    gk.genre_revenue_global,
    gk.genre_rank_global,
    gk.prev_genre_revenue_global,
    case 
        when gk.prev_genre_revenue_global is null or gk.prev_genre_revenue_global = 0 then null
        else (gk.genre_revenue_global - gk.prev_genre_revenue_global) / gk.prev_genre_revenue_global
    end as genre_revenue_global_growth_pct

from genre_country_kpi gc
left join country_kpi ck
    on gc.revenue_month = ck.revenue_month
   and gc.country = ck.country
left join genre_kpi gk
    on gc.revenue_month = gk.revenue_month
   and gc.genre_name = gk.genre_name
