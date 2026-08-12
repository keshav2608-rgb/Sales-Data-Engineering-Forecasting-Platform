with sales as (
    select * from {{ ref('stg_sales') }}
)

select
    product_id,
    any_value(product_name)  as product_name,
    any_value(category)      as category,
    sum(quantity)             as units_sold,
    sum(sales)                as total_revenue
from sales
group by product_id
