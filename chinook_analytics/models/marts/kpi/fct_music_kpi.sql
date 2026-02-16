with genre_country as (
    select *
    from {{ ref('fct_genre_country_month') }}
),

-- Country-level monthly KPIs
country_kpi as (
    select
        revenue_month,
        country,
        sum(total_revenue) as country_revenue,
        rank() over (partition by revenue_month order by sum(total_revenue) desc) as country_rank,
        lag(sum(total_revenue)) over (partition by country order by revenue_month) as prev_month_revenue,
        lag(sum(total_revenue), 12) over (partition by country order by revenue_month) as prev_year_revenue
    from genre_country
    group by revenue_month, country
),

-- Global genre monthly KPIs
genre_kpi as (
    select
        revenue_month,
        genre_name,
        sum(total_revenue) as genre_revenue_global,
        rank() over (partition by revenue_month order by sum(total_revenue) desc) as genre_rank_global,
        lag(sum(total_revenue)) over (partition by genre_name order by revenue_month) as prev_month_genre_revenue_global,
        lag(sum(total_revenue), 12) over (partition by genre_name order by revenue_month) as prev_year_genre_revenue_global
    from genre_country
    group by revenue_month, genre_name
),

-- Top genres per country (Top 5)
genre_country_kpi as (
    select
        revenue_month,
        country,
        genre_name,
        total_revenue as genre_revenue_country,
        genre_market_share_pct,
        genre_market_share_rank
    from genre_country
    where genre_market_share_rank <= 5
),

-- Top customers per country
top_customers as (
    select
        c.customer_id,
        c.country,
        sum(il.unit_price * il.quantity) as lifetime_revenue,
        rank() over (partition by c.country order by sum(il.unit_price * il.quantity) desc) as customer_rank
    from {{ ref('stg_chinook__customer') }} c
    join {{ ref('int_sales__invoice_items') }} il
        on c.customer_id = il.customer_id
    group by c.customer_id, c.country
)

select
    gc.revenue_month,
    gc.country,
    gc.genre_name,

    -- Country KPIs
    ck.country_revenue,
    ck.country_rank,
    ck.prev_month_revenue,
    case when ck.prev_month_revenue is null or ck.prev_month_revenue = 0 then null
         else (ck.country_revenue - ck.prev_month_revenue) / ck.prev_month_revenue
    end as country_mom_growth_pct,
    ck.prev_year_revenue,
    case when ck.prev_year_revenue is null or ck.prev_year_revenue = 0 then null
         else (ck.country_revenue - ck.prev_year_revenue) / ck.prev_year_revenue
    end as country_yoy_growth_pct,

    -- Genre KPIs per country
    gc.genre_revenue_country,
    gc.genre_market_share_pct,
    gc.genre_market_share_rank,

    -- Global genre KPIs
    gk.genre_revenue_global,
    gk.genre_rank_global,
    gk.prev_month_genre_revenue_global,
    case when gk.prev_month_genre_revenue_global is null or gk.prev_month_genre_revenue_global = 0 then null
         else (gk.genre_revenue_global - gk.prev_month_genre_revenue_global) / gk.prev_month_genre_revenue_global
    end as genre_mom_growth_pct,
    gk.prev_year_genre_revenue_global,
    case when gk.prev_year_genre_revenue_global is null or gk.prev_year_genre_revenue_global = 0 then null
         else (gk.genre_revenue_global - gk.prev_year_genre_revenue_global) / gk.prev_year_genre_revenue_global
    end as genre_yoy_growth_pct,

    -- Top customer context
    tc.customer_id as top_customer_id,
    tc.lifetime_revenue as top_customer_ltv,
    tc.customer_rank as top_customer_rank_in_country

from genre_country_kpi gc
left join country_kpi ck
    on gc.revenue_month = ck.revenue_month
   and gc.country = ck.country
left join genre_kpi gk
    on gc.revenue_month = gk.revenue_month
   and gc.genre_name = gk.genre_name
left join top_customers tc
    on gc.country = tc.country
   and tc.customer_rank <= 3  -- top 3 customers per country
