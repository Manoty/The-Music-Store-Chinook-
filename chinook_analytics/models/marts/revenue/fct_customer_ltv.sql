with revenue as (

    select * from {{ ref('int_sales__invoice_items') }}

),

aggregated as (

    select
        customer_id,
        count(distinct invoice_id) as total_orders,
        sum(line_revenue) as lifetime_revenue,
        min(invoice_date) as first_purchase_date,
        max(invoice_date) as last_purchase_date,
        datediff('day', min(invoice_date), max(invoice_date)) as customer_lifetime_days

    from revenue
    group by customer_id

)

select * from aggregated
