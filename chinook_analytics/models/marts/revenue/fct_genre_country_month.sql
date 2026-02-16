ranked as (

    select
        *,
        lag(total_revenue) over (
            partition by country, genre_id
            order by revenue_month
        ) as previous_month_revenue

    from aggregated

),

final as (

    select
        *,
        case
            when previous_month_revenue is null then null
            when previous_month_revenue = 0 then null
            else (total_revenue - previous_month_revenue)
                 / previous_month_revenue
        end as revenue_growth_pct,

        rank() over (
            partition by revenue_month, country
            order by total_revenue desc
        ) as genre_rank_in_country

    from ranked
)

select * from final
