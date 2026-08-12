with dates as (
    select distinct order_date as date_day from {{ ref('stg_sales') }}
)

select
    date_day,
    extract(day from date_day)           as day,
    extract(month from date_day)         as month,
    strftime(date_day, '%B')             as month_name,
    extract(quarter from date_day)       as quarter,
    extract(year from date_day)          as year,
    extract(week from date_day)          as week,
    strftime(date_day, '%A')             as day_of_week,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from dates
