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
        rank() over (partition by revenue_month order by sum(total_revenue) desc) as country_rank
    from genre_country
    group by revenue_month, country
),

-- Top genres per month globally
genre_kpi as (
    select
        revenue_month,
        genre_name,
        sum(total_revenue) as genre_revenue,
        rank() over (partition by revenue_month order by sum(total_revenue) desc) as genre_rank_global
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
    gc.genre_revenue_country,
    gc.genre_market_share_pct,
    gc.genre_market_share_rank,
    ck.country_revenue,
    ck.country_rank,
    gk.genre_revenue as genre_revenue_global,
    gk.genre_rank_global

from genre_country_kpi gc

left join country_kpi ck
    on gc.revenue_month = ck.revenue_month
   and gc.country = ck.country

left join genre_kpi gk
    on gc.revenue_month = gk.revenue_month
   and gc.genre_name = gk.genre_name
