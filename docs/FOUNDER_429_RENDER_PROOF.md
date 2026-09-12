# Render forwarding evidence

Render documents that its load balancer terminates public HTTPS before forwarding traffic to the web service, and that the first IP in `X-Forwarded-For` is the real client IP. Render also sets `RENDER=true` at runtime. This gives OAP a bounded way to derive a client-specific limiter key on Render without trusting forwarded headers in unrelated environments.
