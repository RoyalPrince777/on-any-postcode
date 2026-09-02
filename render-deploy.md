Render deploy steps (quick)
1. Create a new Git repo (or use existing).
   - Add main.py, requirements.txt, smi_chat_streaming.js and this file to the repo root (or appropriate static folder for the JS).

2. Create a new Web Service on Render:
   - Environment: Python 3.10+ (choose supported runtime)
   - Build Command: (leave empty) or `pip install -r requirements.txt`
   - Start Command:
     uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers

   (Alternatively, use gunicorn with uvicorn workers:
     gunicorn -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:$PORT
   )

3. Set instance size/timeouts:
   - For streaming, prefer at least 1GB mem and a few concurrency workers.
   - Increase request timeout if you stream long-running responses (Render has platform timeouts).

4. Important proxy/buffering notes:
   - The response includes header `X-Accel-Buffering: no` to advise proxies not to buffer.
   - Some hosts/CDNs still buffer; if you see responses arriving only at the end, verify host/proxy settings or contact Render support about proxy buffering and response streaming.
   - Avoid response compression that forces full buffering. If you must, ensure chunked responses are not fully buffered.

5. Test locally:
   - pip install -r requirements.txt
   - uvicorn main:app --host 0.0.0.0 --port 8000
   - Test with curl (use -N to disable curl buffering):
     curl -N -X POST -F "message=Hello streaming world from server!" http://localhost:8000/stream

   You should see SSE-style "data: {...}" chunks as they are produced.

6. Client:
   - Use the streaming-capable JS client `smi_chat_streaming.js`.
   - Ensure the page sets `streamUrl` to the /stream endpoint, and `csrfToken` if needed.
   - Example in template:
     <script>const streamUrl = {{ url_for('stream')|tojson }};</script>
     <script src="{{ url_for('static', filename='smi_chat_streaming.js') }}"></script>

7. Production considerations:
   - Validate auth/CSRF before starting long-lived streaming.
   - Ensure your model-generation code can be cancelled early (check request.is_disconnected()) and releases resources on abort.
   - Add logging/monitoring (Sentry) to track failed or aborted streams.
