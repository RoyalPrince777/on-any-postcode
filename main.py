"""
FastAPI streaming endpoint (SSE) for assistant responses.

POST /stream
- Accepts multipart/form-data (message, optional files)
- Streams Server-Sent Events (SSE) with JSON payloads:
  data: {"type":"delta","content":"...","seq":n}
  data: {"type":"done","seq":n+1}

Integrate your model/token stream generator in `generate_tokens`.
"""
import json
import asyncio
from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Optional, List

app = FastAPI(title="SMI Stream API")


async def generate_tokens(message: str) -> AsyncGenerator[str, None]:
    """
    Placeholder token generator.
    Replace this with your model's async token stream.
    Yields small text chunks (strings).
    """
    # Simple demo: split message into chunks
    chunk_size = 8
    for i in range(0, len(message), chunk_size):
        await asyncio.sleep(0.03)  # simulate latency / model work
        yield message[i : i + chunk_size]
    # If you integrate with a model that yields tokens, yield tokens here instead.


async def sse_event_generator(request: Request, message: str):
    """
    Streams SSE 'data: <json>\n\n' blocks until done or client disconnect.
    Checks request.is_disconnected() to stop early if client aborts.
    """
    seq = 0
    try:
        async for token in generate_tokens(message):
            # Stop if client disconnected
            if await request.is_disconnected():
                # optional: do any cleanup if needed
                break
            seq += 1
            payload = json.dumps({"type": "delta", "content": token, "seq": seq})
            yield f"data: {payload}\n\n"
        # final done event
        if not await request.is_disconnected():
            seq += 1
            yield f"data: {json.dumps({'type': 'done', 'seq': seq})}\n\n"
    except asyncio.CancelledError:
        # client disconnected or server aborted
        return
    except Exception as e:
        # Signal error to client
        try:
            payload = json.dumps({"type": "error", "content": str(e)})
            yield f"data: {payload}\n\n"
        except Exception:
            pass


@app.post("/stream")
async def stream_endpoint(request: Request):
    """
    Example streaming endpoint.
    Expects form-data with 'message' (string). Files are accepted but not stored in this demo.
    """
    # Parse form data safely
    form = await request.form()
    message: Optional[str] = form.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message' form field")

    generator = sse_event_generator(request, message)
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # many proxies honor this header to disable buffering:
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(generator, media_type="text/event-stream", headers=headers)


@app.get("/health")
async def health():
    return {"status": "ok"}
