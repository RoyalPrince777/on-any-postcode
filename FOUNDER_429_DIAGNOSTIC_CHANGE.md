# Founder 429 diagnostic change

This branch adds only evidence-gathering and safety checks for the Founder HTTP 429 incident. It intentionally does not change application authentication, gateway allowlists, production configuration, rate limits, Render settings, or deployment state.

The diagnostic probe performs two anonymous bounded GET requests and prints status plus selected response headers. It never submits Founder credentials.
