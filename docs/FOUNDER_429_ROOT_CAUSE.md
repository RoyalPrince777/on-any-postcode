# Founder 429 root cause candidate

The current Founder sign-in limiter key uses `request.remote_addr`. On Render, inbound HTTPS is terminated at Render's load balancer and Render documents the original client IP in the first `X-Forwarded-For` entry. Keying solely on the socket peer can therefore collapse distinct requests onto the proxy/load-balancer address and create false shared 429 lockouts.

Any fix must trust forwarded client IP only when the runtime is known to be Render (`RENDER=true`), otherwise fall back to the direct socket address.
