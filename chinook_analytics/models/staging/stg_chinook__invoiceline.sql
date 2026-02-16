with source as (

    select * from {{ source('chinook', 'invoiceline') }}

),

renamed as (

    select
        invoicelineid as invoice_line_id,
        invoiceid as invoice_id,
        trackid as track_id,
        unitprice as unit_price,
        quantity as quantity

    from source

)

select * from renamed
