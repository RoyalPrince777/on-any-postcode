# OAP Commerce Secure Provider Install Contract

This contract intentionally contains variable names only. Never commit real provider
names, account identifiers, API tokens, webhook secrets, or private credentials.

## Database / install

- DATABASE_URL
- OAP_COMMERCE_MIGRATION_ON_BOOT=true

The boot migration is opt-in. It applies the first-party Supplier Network, SIKA payment
intent, submission evidence, Distribution Runtime, and provider receipt schemas.

## Payment provider

- OAP_PAYMENT_PROVIDER_ID
- OAP_PAYMENT_PROVIDER_BASE_URL
- OAP_PAYMENT_PROVIDER_ALLOWED_HOST
- OAP_PAYMENT_PROVIDER_TOKEN
- OAP_PAYMENT_PROVIDER_WEBHOOK_SECRET
- OAP_PAYMENT_PROVIDER_SUBMIT_PATH
- OAP_PAYMENT_PROVIDER_REFUND_PATH
- OAP_PAYMENT_PROVIDER_EXECUTION_ENABLED=true

## Print-on-Demand provider

- OAP_POD_PROVIDER_ID
- OAP_POD_PROVIDER_BASE_URL
- OAP_POD_PROVIDER_ALLOWED_HOST
- OAP_POD_PROVIDER_TOKEN
- OAP_POD_PROVIDER_WEBHOOK_SECRET
- OAP_POD_PROVIDER_SUBMIT_PATH
- OAP_POD_PROVIDER_EXECUTION_ENABLED=true

## Provider webhook contract

OAP expects the raw request body to be signed with HMAC-SHA256 using the configured
webhook secret over:

`<unix_timestamp>.<raw_body>`

Headers:

- X-OAP-Provider-Timestamp
- X-OAP-Provider-Signature

The signature may be sent as the bare hexadecimal digest or with a `sha256=` prefix.
The timestamp must be within the configured runtime replay window.

## Runtime routes

Founder-controlled:

- GET /mission/organs/market/install-status
- POST /mission/organs/market/install
- POST /mission/organs/market/payments/<payment_id>/execute
- POST /mission/organs/market/pod/<subject_id>/execute

Signed provider callbacks:

- POST /mission/organs/market/payments/provider/webhook
- POST /mission/organs/market/pod/provider/webhook

Provider credentials are added only in the deployment secret store. They are not
returned by status endpoints or stored in provider receipts.
