with sales as (
    select * from {{ ref('stg_sales') }}
)

select
    customer_id,
    any_value(customer_name)  as customer_name,
    count(distinct order_id)  as order_count,
    sum(sales)                as total_revenue,
    min(order_date)           as first_order_date,
    max(order_date)           as last_order_date
from sales
group by customer_id
