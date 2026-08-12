with sales as (
    select * from {{ ref('stg_sales') }}
),
cust as (
    select customer_key, customer_id from {{ ref('dim_customer') }}
),
prod as (
    select product_key, product_id from {{ ref('dim_product') }}
)

select
    row_number() over (order by sales.order_id) as sale_id,
    sales.order_id,
    sales.order_date                            as date_key,
    cust.customer_key,
    prod.product_key,
    sales.region,
    sales.country,
    sales.quantity,
    sales.unit_price,
    sales.discount,
    sales.sales as revenue
from sales
left join cust using (customer_id)
left join prod using (product_id)
