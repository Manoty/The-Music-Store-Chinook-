with base as (

    select * from {{ ref('int_sales_genre_revenue') }}

),

aggregated as (

    select
        date_trunc('month', invoice_date) as revenue_month,
        country,
        genre_id,
        genre_name,
        count(distinct invoice_id) as total_orders,
        sum(line_revenue) as total_revenue
    from base
    group by 1,2,3,4

),

with_country_totals as (

    select
        *,
        sum(total_revenue) over (
            partition by revenue_month, country
        ) as total_country_revenue
    from aggregated

),

ranked as (

    select
        *,
        lag(total_revenue) over (
            partition by country, genre_id
            order by revenue_month
        ) as previous_month_revenue
    from with_country_totals

),

final as (

    select
        revenue_month,
        country,
        genre_id,
        genre_name,
        total_orders,
        total_revenue,
        total_country_revenue,

        -- Month-over-month growth %
        case
            when previous_month_revenue is null then null
            when previous_month_revenue = 0 then null
            else (total_revenue - previous_month_revenue) / previous_month_revenue
        end as revenue_growth_pct,

        -- Market share %
        case
            when total_country_revenue = 0 then null
            else total_revenue / total_country_revenue
        end as genre_market_share_pct,

        -- Market share rank (highest first)
        dense_rank() over (
            partition by revenue_month, country
            order by 
                case when total_country_revenue = 0 then 0 
                     else total_revenue / total_country_revenue end desc
        ) as genre_market_share_rank

    from ranked

)

select * from final
