-- Synthetic "expensive join" the spike uses to exercise the rewrite path.
-- The pathology: a date filter sits on the outer query but could be pushed
-- into both fact tables, and SELECT * forces unnecessary column scans.
SELECT *
FROM analytics.public.orders o
JOIN analytics.public.customers c ON c.customer_id = o.customer_id
JOIN analytics.public.line_items li ON li.order_id = o.order_id
JOIN analytics.public.products p ON p.product_id = li.product_id
WHERE o.order_ts >= '2025-01-01'
  AND o.order_ts <  '2025-02-01'
  AND c.region = 'NA';
