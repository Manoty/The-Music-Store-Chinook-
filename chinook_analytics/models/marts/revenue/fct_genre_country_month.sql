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

ranked as (

    select
        *,
        rank() over (
            partition by revenue_month, country
            order by total_revenue desc
        ) as genre_rank_in_country

    from aggregated

)

select * from ranked
