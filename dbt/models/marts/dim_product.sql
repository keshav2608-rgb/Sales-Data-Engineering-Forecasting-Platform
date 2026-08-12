select
    row_number() over (order by product_id) as product_key,
    product_id,
    product_name,
    category,
    units_sold,
    total_revenue
from {{ ref('int_product_sales') }}
