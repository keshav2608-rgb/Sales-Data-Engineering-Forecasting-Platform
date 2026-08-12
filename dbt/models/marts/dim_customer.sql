with cust as (
    select * from {{ ref('int_customer_sales') }}
),
sales as (
    select customer_id, any_value(segment) as segment, any_value(region) as region
    from {{ ref('stg_sales') }}
    group by customer_id
)

select
    row_number() over (order by cust.customer_id) as customer_key,
    cust.customer_id,
    cust.customer_name,
    sales.segment,
    sales.region,
    cust.order_count,
    cust.total_revenue,
    case when cust.order_count > 1 then true else false end as is_repeat_customer
from cust
left join sales using (customer_id)
