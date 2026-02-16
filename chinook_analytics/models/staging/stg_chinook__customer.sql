with source as (

    select * from {{ source('chinook', 'customer') }}

),

renamed as (

    select
        customerid as customer_id,
        firstname as first_name,
        lastname as last_name,
        company as company,
        address as address,
        city as city,
        state as state,
        country as country,
        postalcode as postal_code,
        phone as phone,
        fax as fax,
        email as email,
        supportrepid as support_rep_id

    from source

)

select * from renamed
