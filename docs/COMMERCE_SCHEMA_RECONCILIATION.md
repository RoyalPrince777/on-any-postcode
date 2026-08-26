# OAP Commerce schema reconciliation

Production already contains legacy `oap_market_items` and `oap_market_orders` tables with an older bigint-based shape. They remain untouched.

The first-party Shopify-style workflow introduced by Product Cores uses the separate `oap_commerce_*` namespace:

- `oap_commerce_storefronts`
- `oap_commerce_orders`
- `oap_commerce_order_items`
- `oap_commerce_payment_intents`
- `oap_commerce_fulfilment_intents`

This avoids destructive alteration or reinterpretation of legacy Market data. Payment capture and third-party fulfilment remain provider-gated. The product-core migration remains explicit and checksum-gated, and migration version `0006_music_market_post_office` is safe to revise because it has not been applied to production.
