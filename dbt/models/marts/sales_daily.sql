select
    date_key                       as order_date,
    count(distinct order_id)       as total_orders,
    sum(quantity)                  as total_units,
    sum(revenue)                   as total_revenue,
    round(sum(revenue) / nullif(count(distinct order_id), 0), 2) as avg_order_value
from {{ ref('fact_sales') }}
group by date_key
order by date_key
