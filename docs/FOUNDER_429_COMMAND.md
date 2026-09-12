# Single handset command

```sh
curl -sS -o /dev/null -D - 'https://oap-smi.onrender.com/auth/recover-founder?next=/mission/ollama' | grep -Ei '^(HTTP/|retry-after:|server:|via:|x-request-id:|cf-ray:|x-render-)'
```

This does not submit a password. Use the full branch probe when comparing both routes.
