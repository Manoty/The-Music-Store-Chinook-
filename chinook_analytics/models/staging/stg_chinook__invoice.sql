with source as (

    select * from {{ source('chinook', 'invoice') }}

),

renamed as (

    select
        invoiceid as invoice_id,
        customerid as customer_id,
        invoicedate as invoice_date,
        billingaddress as billing_address,
        billingcity as billing_city,
        billingstate as billing_state,
        billingcountry as billing_country,
        billingpostalcode as billing_postal_code,
        total as total_amount

    from source

)

select * from renamed
