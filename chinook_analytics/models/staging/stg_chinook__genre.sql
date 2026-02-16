with source as (

    select * from {{ source('chinook', 'genre') }}

),

renamed as (

    select
        genreid as genre_id,
        name as name

    from source

)

select * from renamed
