with invoice_line as (

    select * from {{ ref('stg_chinook__invoiceline') }}

),

invoice as (

    select * from {{ ref('stg_chinook__invoice') }}

),

joined as (

    select
        il.invoice_line_id,
        il.invoice_id,
        i.customer_id,
        i.invoice_date,
        il.track_id,
        il.unit_price,
        il.quantity,
        il.unit_price * il.quantity as line_revenue

    from invoice_line il
    left join invoice i
        on il.invoice_id = i.invoice_id

)

select * from joined
