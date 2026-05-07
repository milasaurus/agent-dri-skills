-- What a competent rewrite looks like for fixtures/expensive_join.sql.
-- Used by test_rewriter.py to grade the LLM output offline.
-- Differences from the original:
--   1. Date filter is mirrored onto line_items via a join condition derived
--      from orders, so partition pruning kicks in on both fact tables.
--   2. Explicit projection — analyst only needs these columns downstream.
SELECT
    o.order_id,
    o.order_ts,
    c.customer_id,
    c.region,
    li.line_item_id,
    li.quantity,
    p.product_name,
    p.category
FROM analytics.public.orders o
JOIN analytics.public.customers c
  ON c.customer_id = o.customer_id
 AND c.region = 'NA'
JOIN analytics.public.line_items li
  ON li.order_id = o.order_id
 AND li.order_ts >= '2025-01-01'
 AND li.order_ts <  '2025-02-01'
JOIN analytics.public.products p
  ON p.product_id = li.product_id
WHERE o.order_ts >= '2025-01-01'
  AND o.order_ts <  '2025-02-01';
