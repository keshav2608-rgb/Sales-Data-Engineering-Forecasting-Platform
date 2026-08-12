with source as (
    select * from {{ source('raw', 'sales_staging') }}
)

select
    order_id,
    cast(order_date as date)      as order_date,
    customer_id,
    customer_name,
    product_id,
    product_name,
    category,
    region,
    country,
    segment,
    cast(quantity as integer)     as quantity,
    cast(unit_price as double)    as unit_price,
    cast(discount as double)      as discount,
    cast(sales as double)         as sales
from source
