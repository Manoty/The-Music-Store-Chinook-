with source as (

    select * from {{ source('chinook', 'track') }}

),

renamed as (

    select
        trackid as track_id,
        name as track_name,
        albumid as album_id,
        mediatypeid as media_type_id,
        genreid as genre_id,
        composer as composer,
        milliseconds as milliseconds,
        

    from source

)

select * from renamed
