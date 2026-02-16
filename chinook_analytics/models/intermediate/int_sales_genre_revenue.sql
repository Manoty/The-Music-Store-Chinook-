with invoice_items as (

    select * from {{ ref('int_sales__invoice_items') }}

),

track as (

    select * from {{ ref('stg_chinook__track') }}

),

genre as (

    select * from {{ ref('stg_chinook__genre') }}

),

customer as (

    select * from {{ ref('stg_chinook__customer') }}

),

joined as (

    select
        ii.invoice_id,
        ii.customer_id,
        c.country,
        ii.invoice_date,
        t.genre_id,
        g.name as genre_name,
        ii.line_revenue

    from invoice_items ii

    left join customer c
        on ii.customer_id = c.customer_id

    left join track t
        on ii.track_id = t.track_id

    left join genre g
        on t.genre_id = g.genre_id

)

select * from joined
