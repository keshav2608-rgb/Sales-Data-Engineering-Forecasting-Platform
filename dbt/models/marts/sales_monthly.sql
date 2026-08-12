with monthly as (
    select
        date_trunc('month', date_key)  as month_start,
        count(distinct order_id)       as total_orders,
        sum(revenue)                   as total_revenue
    from {{ ref('fact_sales') }}
    group by 1
)

select
    month_start,
    total_orders,
    total_revenue,
    round(
        100.0 * (total_revenue - lag(total_revenue) over (order by month_start))
        / nullif(lag(total_revenue) over (order by month_start), 0), 2
    ) as mom_growth_pct,
    round(
        100.0 * (total_revenue - lag(total_revenue, 12) over (order by month_start))
        / nullif(lag(total_revenue, 12) over (order by month_start), 0), 2
    ) as yoy_growth_pct
from monthly
order by month_start
