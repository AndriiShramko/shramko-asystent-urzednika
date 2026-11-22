"""AUDIT-8 VC-10 (06-F4): a slow upload must not hold a processing slot while its body is still arriving. With one
slot, a client that sends its body slowly made every other convert 429 BUSY until its upload ended."""
from __future__ import annotations

import asyncio

import factory as fx
import httpx

from app.config import Settings
from app.main import create_app

BOUNDARY = "a8vc10boundary"


def multipart(name: str, data: bytes) -> bytes:
    head = (f"--{BOUNDARY}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
            "Content-Type: application/pdf\r\n\r\n").encode()
    return head + data + f"\r\n--{BOUNDARY}--\r\n".encode()


def test_a_slow_upload_does_not_make_others_busy():
    env = {"AUTH_MODE": "off", "UI_ENABLED": "false", "RATE_LIMIT_PER_MIN": "100000", "CONCURRENCY": "1"}
    app = create_app(Settings.from_env(env))
    body = multipart("slow.pdf", fx.pdf())
    headers = {"content-type": f"multipart/form-data; boundary={BOUNDARY}"}

    async def slow_body():
        yield body[:200]
        await asyncio.sleep(1.5)   # the rest of the upload arrives late
        yield body[200:]

    async def main():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t", timeout=60) as c:
            slow = asyncio.create_task(c.post("/v1/forms/convert", content=slow_body(),
                                              headers={**headers, "content-length": str(len(body))}))
            await asyncio.sleep(0.3)   # the slow client is now inside its upload
            fast = await c.post("/v1/forms/convert", files={"file": ("a.pdf", fx.pdf(), "application/pdf")})
            await slow
            return fast

    fast = asyncio.run(main())
    assert fast.status_code == 200, fast.text
