"""Smoke test of the deck via Chrome DevTools Protocol (no Playwright needed).
Usage: python -X utf8 deck_smoke.py [--deck DIR] [--out DIR] [--presenter-slide N] [slides...]
  default deck: site/deck, screenshots: docs/assets/deck (paths relative to the repo root)
  e.g. deck_smoke.py 8 9                (only slides 8 and 9)
       deck_smoke.py --deck site-formularze/deck --out docs/assets/deck-formularze --presenter-slide 4
  Without slide numbers: all slides + presenter + answer card + print check + contact sheet.
  The last slide's screenshot is scanned for a QR code.
"""
import asyncio, base64, json, os, re, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
import websockets
import numpy as np, cv2
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def opt(name, default):
    if name in sys.argv:
        i = sys.argv.index(name); v = sys.argv[i + 1]; del sys.argv[i:i + 2]; return v
    return default
DECK_DIR = (ROOT / opt("--deck", "site/deck")).resolve()
OUT = (ROOT / opt("--out", "docs/assets/deck")).resolve()
PRESENTER_SLIDE = int(opt("--presenter-slide", "5"))
DECK = DECK_DIR / "index.html"
OUT.mkdir(parents=True, exist_ok=True)
URL = DECK.as_uri()
PORT = int(opt("--port", "9339"))  # use another port if a second smoke run may be active
only = [int(a) for a in sys.argv[1:] if a.isdigit()]
OPTIONAL_VIDEO = re.compile(r"demo(-\d+)?\.mp4")  # optional demo videos absent: expected

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
                if not OPTIONAL_VIDEO.search(e["params"]["entry"].get("url", "") + txt):
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
        # test the animated deck even when the OS has animations off (Windows: reduce motion -> still frames)
        await c.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-reduced-motion", "value": "no-preference"}])
        await c.call("Page.navigate", url=URL); await c.drain(1.0)
        total = (await c.call("Runtime.evaluate", expression="window.DECK.slides.length"))["result"]["value"]
        slides = only or list(range(1, total + 1))
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
            await c.call("Page.navigate", url=f"{URL}?presenter=1#{PRESENTER_SLIDE}"); await c.drain(1.5)
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
    # QR decode from the actual screenshot of the last slide
    last = OUT / f"slide-{total:02d}.png"
    if last.exists():
        img = cv2.imread(str(last))
        report.append("QR from screenshot: " + repr(cv2.QRCodeDetector().detectAndDecode(img)[0]))
    if not only:
        ims = [Image.open(OUT / f"slide-{n:02d}.png").convert("RGB").resize((640, 360)) for n in range(1, total + 1)]
        nrows = (total + 2) // 3
        sheet = Image.new("RGB", (3 * 640 + 4 * 16, nrows * 360 + (nrows + 1) * 16), (11, 16, 32))
        for k, im in enumerate(ims):
            sheet.paste(im, (16 + (k % 3) * 656, 16 + (k // 3) * 376))
        sheet.save(OUT / "contact-sheet.png", optimize=True)
    print("\n".join(report))

asyncio.run(main())
