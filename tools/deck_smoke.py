"""Smoke test of the deck via Chrome DevTools Protocol (no Playwright needed).
Usage: python -X utf8 smoke.py [slides...]   e.g. smoke.py 8 9   (default: all + presenter + sheet)
"""
import asyncio, base64, json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
import websockets
import numpy as np, cv2
from PIL import Image

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
DECK = Path(r"C:\dev\shramko-asystent-urzednika\site\deck\index.html")
OUT = Path(r"C:\dev\shramko-asystent-urzednika\docs\assets\deck")
OUT.mkdir(parents=True, exist_ok=True)
URL = DECK.as_uri()
PORT = 9339
only = [int(a) for a in sys.argv[1:] if a.isdigit()]

class CDP:
    def __init__(s, ws): s.ws, s.i, s.events, s.pending = ws, 0, [], {}
    async def call(s, method, **params):
        s.i += 1; my = s.i
        await s.ws.send(json.dumps({"id": my, "method": method, "params": params}))
        while True:
            m = json.loads(await s.ws.recv())
            if m.get("id") == my:
                if "error" in m: raise RuntimeError(m["error"])
                return m.get("result", {})
            s.events.append(m)
    async def drain(s, secs):
        end = time.time() + secs
        while time.time() < end:
            try:
                m = json.loads(await asyncio.wait_for(s.ws.recv(), timeout=max(0.05, end - time.time())))
                s.events.append(m)
            except asyncio.TimeoutError:
                pass
    def errors(s):
        errs = []
        for e in s.events:
            mth = e.get("method")
            if mth == "Runtime.exceptionThrown":
                errs.append(e["params"]["exceptionDetails"].get("exception", {}).get("description", "exception"))
            elif mth == "Runtime.consoleAPICalled" and e["params"]["type"] in ("error", "assert"):
                errs.append(str(e["params"]["args"]))
            elif mth == "Log.entryAdded" and e["params"]["entry"]["level"] == "error":
                txt = e["params"]["entry"]["text"]
                if "demo.mp4" not in e["params"]["entry"].get("url", "") + txt:  # optional video absent: expected
                    errs.append(txt)
        s.events = []
        return errs

async def shot(c, path, w, h):
    r = await c.call("Page.captureScreenshot", format="png", clip={"x": 0, "y": 0, "width": w, "height": h, "scale": 1})
    data = base64.b64decode(r["data"]); Path(path).write_bytes(data); return data

def diff(a, b):
    ia = cv2.imdecode(np.frombuffer(a, np.uint8), 0).astype(int); ib = cv2.imdecode(np.frombuffer(b, np.uint8), 0).astype(int)
    return int((abs(ia - ib) > 12).sum())

async def main():
    prof = tempfile.mkdtemp(prefix="deck-smoke-")
    p = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={PORT}", f"--user-data-dir={prof}",
                          "--no-first-run", "--hide-scrollbars", "--autoplay-policy=no-user-gesture-required", "about:blank"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json")); break
        except Exception: time.sleep(0.2)
    ws_url = [t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"]
    report = []
    async with websockets.connect(ws_url, max_size=50_000_000) as ws:
        c = CDP(ws)
        for m in ("Page.enable", "Runtime.enable", "Log.enable"): await c.call(m)
        await c.call("Emulation.setDeviceMetricsOverride", width=1280, height=720, deviceScaleFactor=1, mobile=False)
        slides = only or list(range(1, 12))
        for n in slides:
            await c.call("Page.navigate", url="about:blank"); await c.drain(0.3); c.events = []
            await c.call("Page.navigate", url=f"{URL}#{n}")
            await c.drain(11.0)
            a = await shot(c, OUT / f"slide-{n:02d}.png", 1280, 720)
            await c.drain(1.3)
            b = await shot(c, Path(tempfile.gettempdir()) / "deck-b.png", 1280, 720)
            report.append(f"slide {n}: errors={c.errors()} moving_px={diff(a, b)}")
        if not only:
            await c.call("Emulation.setDeviceMetricsOverride", width=1280, height=800, deviceScaleFactor=1, mobile=False)
            await c.call("Page.navigate", url="about:blank"); await c.drain(0.3)
            await c.call("Page.navigate", url=f"{URL}?presenter=1#5"); await c.drain(1.5)
            await shot(c, OUT / "presenter.png", 1280, 800)
            for typ in ("keyDown", "keyUp"):
                await c.call("Input.dispatchKeyEvent", type=typ, key="3", code="Digit3", windowsVirtualKeyCode=51)
            await c.drain(0.6)
            await shot(c, OUT / "presenter-answer.png", 1280, 800)
            report.append(f"presenter: errors={c.errors()}")
            # print mode loads too
            await c.call("Page.navigate", url=f"{URL}?print=1"); await c.drain(1.5)
            r = await c.call("Runtime.evaluate", expression="document.querySelectorAll('.page').length")
            report.append(f"print pages={r['result'].get('value')} errors={c.errors()}")
    p.terminate()
    # QR decode from the actual slide 11 screenshot
    img = cv2.imread(str(OUT / "slide-11.png"))
    report.append("QR from screenshot: " + repr(cv2.QRCodeDetector().detectAndDecode(img)[0]))
    if not only:
        ims = [Image.open(OUT / f"slide-{n:02d}.png").convert("RGB").resize((640, 360)) for n in range(1, 12)]
        sheet = Image.new("RGB", (3 * 640 + 4 * 16, 4 * 360 + 5 * 16), (11, 16, 32))
        for k, im in enumerate(ims):
            sheet.paste(im, (16 + (k % 3) * 656, 16 + (k // 3) * 376))
        sheet.save(OUT / "contact-sheet.png", optimize=True)
    print("\n".join(report))

asyncio.run(main())
