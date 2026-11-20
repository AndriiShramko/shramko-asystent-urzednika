#!/usr/bin/env python3
"""Re-runnable crawler: service cards and form templates of Urzad Miasta Bydgoszczy.

Sources
  (a) e-urzad portal https://um.bydgoszcz.pl/  (index pages /alfabetycznie/,
      /wedlug-wydzialow/, /wedlug-kategorii/ + category and subcategory pages,
      then every card /sprawa/<category-id>/<slug>/)
  (b) BIP pages with templates (https://bip.um.bydgoszcz.pl/artykul/...)

Output
  data/forms-catalog.json  cards (+ attachments, checks) and BIP pages
  data/forms-catalog.csv   one row per attachment

Politeness: robots.txt is read first and respected, max 2 requests/second,
timeout 20 s, 2 retries, fixed User-Agent. Binaries are never stored unless
--download DIR is given.

Usage
  python tools/crawl_bydgoszcz_forms.py                 # full crawl
  python tools/crawl_bydgoszcz_forms.py --max-cards 20  # quick test
  python tools/crawl_bydgoszcz_forms.py --no-head       # skip attachment checks
  python tools/crawl_bydgoszcz_forms.py --extra-urls urls.txt  # extra URLs to HEAD-check
  python tools/crawl_bydgoszcz_forms.py --download cache/forms
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
from collections import OrderedDict
from urllib.parse import urljoin, urlparse, unquote

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    print("requires: requests, beautifulsoup4 (pip install --user requests beautifulsoup4)")
    sys.exit(2)

UA = "Mozilla/5.0 (compatible; forms-catalog-research)"
PORTAL = "https://um.bydgoszcz.pl"
BIP = "https://bip.um.bydgoszcz.pl"
TIMEOUT = 20
MIN_INTERVAL = 0.5  # seconds -> max 2 requests/second
FILE_EXT = {"pdf", "doc", "docx", "rtf", "odt", "ods", "xls", "xlsx", "zip", "txt", "jpg", "png", "xml", "xsd", "odp", "ppt", "pptx"}
BIP_PAGES = [
    "/artykul/1052/2/udostepnianie-informacji-publicznej",
    "/artykul/1053/1/ponowne-wykorzystanie-informacji-publicznej",
    "/artykul/1009/574/wnioski-w-sprawach-podatkow-i-oplat-lokalnych",
    "/artykul/1257/848",
    "/artykul/1247/572/formularze-podatkowe",
    "/artykul/1372/4613/wzory-wnioskow",
    "/artykul/1482/9091/skargi-i-wnioski",
    "/artykul/1009/9251",
]
BIP_KEYWORDS = re.compile(r"wniosk|wzor|formularz|druk|skarg|deklaracj|podanie|oswiadczen", re.I)
EXTERNAL_RE = re.compile(r"(gov\.pl|epuap|obywatel|pwpw|biznes\.gov|doreczen|ekrs|ceidg|pz\.gov)", re.I)
DATE_RE = re.compile(r"(?:aktualizacj\w*|zmian\w*|data modyfikacji|ostatnia modyfikacja)[^0-9]{0,40}(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}|\d{4}-\d{2}-\d{2})", re.I)


class Fetcher:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.last = 0.0
        self.robots = {}
        self.n = 0

    def _wait(self):
        d = MIN_INTERVAL - (time.monotonic() - self.last)
        if d > 0:
            time.sleep(d)
        self.last = time.monotonic()

    def load_robots(self, base):
        host = urlparse(base).netloc
        if host in self.robots:
            return
        rules = []
        try:
            self._wait()
            r = self.s.get(base + "/robots.txt", timeout=TIMEOUT)
            applies = False
            if r.status_code == 200:
                for line in r.text.splitlines():
                    line = line.split("#")[0].strip()
                    if ":" not in line:
                        continue
                    k, v = [x.strip() for x in line.split(":", 1)]
                    if k.lower() == "user-agent":
                        applies = (v == "*")
                    elif applies and k.lower() == "disallow" and v:
                        rules.append(v)
        except requests.RequestException:
            pass
        self.robots[host] = rules

    def allowed(self, url):
        p = urlparse(url)
        self.load_robots(f"{p.scheme}://{p.netloc}")
        path = p.path + ("?" + p.query if p.query else "")
        for rule in self.robots.get(p.netloc, []):
            pat = re.escape(rule).replace(r"\*", ".*")
            if rule.endswith("$"):
                pat = pat[:-2] + "$"
            if re.match(pat, path):
                return False
        return True

    def request(self, method, url, **kw):
        if not self.allowed(url):
            return None, "blocked by robots.txt"
        err = ""
        for attempt in range(3):  # first try + 2 retries
            try:
                self._wait()
                self.n += 1
                r = self.s.request(method, url, timeout=TIMEOUT, allow_redirects=True, **kw)
                return r, ""
            except requests.RequestException as e:
                err = type(e).__name__ + ": " + str(e)[:120]
                time.sleep(1.5 * (attempt + 1))
        return None, err

    def get_soup(self, url):
        r, err = self.request("GET", url)
        if r is None or r.status_code != 200:
            return None, (r.status_code if r is not None else err)
        r.encoding = r.encoding or "utf-8"
        return BeautifulSoup(r.content.decode("utf-8", errors="replace"), "html.parser"), 200

    def check_file(self, url):
        """HEAD, fallback streamed GET. Returns dict http_status, content_type, content_length, final_url."""
        out = {"http_status": None, "content_type": None, "content_length": None, "final_url": None, "error": ""}
        r, err = self.request("HEAD", url)
        if r is None or r.status_code in (403, 405, 501) or r.status_code >= 400 or not r.headers.get("Content-Type"):
            r2, err2 = self.request("GET", url, stream=True)
            if r2 is not None:
                r = r2
                err = ""
            elif r is None:
                out["error"] = err2 or err
                return out
        if r is None:
            out["error"] = err
            return out
        out["http_status"] = r.status_code
        out["content_type"] = (r.headers.get("Content-Type") or "").split(";")[0].strip() or None
        cl = r.headers.get("Content-Length")
        if cl is None and r.request.method == "GET":
            # count bytes without keeping them (limited to 25 MB)
            n = 0
            try:
                for chunk in r.iter_content(65536):
                    n += len(chunk)
                    if n > 25_000_000:
                        break
                cl = str(n)
            except requests.RequestException:
                pass
        out["content_length"] = int(cl) if cl and str(cl).isdigit() else None
        out["final_url"] = r.url
        if r.request.method == "GET":
            r.close()
        return out


def ext_of(url, label=""):
    path = unquote(urlparse(url).path)
    m = re.search(r"\.([A-Za-z0-9]{2,5})$", path)
    if m and m.group(1).lower() in FILE_EXT:
        return m.group(1).lower()
    m = re.search(r"\(([A-Za-z]{3,4})\)\s*$", label or "")
    if m and m.group(1).lower() in FILE_EXT:
        return m.group(1).lower()
    return ""


def norm(t):
    return re.sub(r"\s+", " ", t or "").strip()


def section_text(soup, heading_regex, limit=1200):
    """Text of the collapsible card section (button.section__title + div.section__body) whose title matches."""
    for btn in soup.find_all("button", class_="section__title"):
        if re.search(heading_regex, norm(btn.get_text()), re.I):
            body = soup.find(id=(btn.get("data-target") or "").lstrip("#"))
            if body is not None:
                return norm(body.get_text(" "))[:limit]
    return ""


def parse_listing(soup, base):
    """Cards in an index page: {url: {code,title,online_icons}}"""
    cards = OrderedDict()
    for li in soup.find_all("li", class_="service-card-list__item"):
        a = li.find("a", href=re.compile(r"/sprawa/\d+/"))
        if not a:
            continue
        url = urljoin(base, a["href"])
        code = norm(li.find("span", class_="badge").get_text()) if li.find("span", class_="badge") else ""
        name = li.find("div", class_="service-card-list__name")
        ext = [urljoin(base, x["href"]) for x in li.find_all("a", href=re.compile(r"^https?://"))]
        cards[url] = {"code": code, "title": norm(name.get_text()) if name else "", "listing_external": ext}
    for a in soup.select("ul.subcategory-card-list li a[href]"):
        if not re.search(r"/sprawa/\d+/", a["href"]):
            continue
        url = urljoin(base, a["href"])
        b = a.find("span", class_="badge")
        code = norm(b.get_text()) if b else ""
        title = norm(a.get_text()).replace(code, "", 1).strip() if code else norm(a.get_text())
        cards.setdefault(url, {"code": code, "title": title, "listing_external": []})
    return cards


def crawl_portal(f, max_cards=None, log=print):
    log("portal: index pages")
    index = {}
    meta = {}  # url -> dict(departments, categories)

    def add(url, info, key=None, val=None):
        m = meta.setdefault(url, {"code": "", "title": "", "departments": [], "categories": [], "listing_external": []})
        for k in ("code", "title"):
            if info.get(k) and not m[k]:
                m[k] = info[k]
        for e in info.get("listing_external", []):
            if e not in m["listing_external"]:
                m["listing_external"].append(e)
        if key and val and val not in m[key]:
            m[key].append(val)

    # alphabetical index = complete list of cards
    soup, st = f.get_soup(PORTAL + "/alfabetycznie/")
    if soup is None:
        raise SystemExit(f"cannot load /alfabetycznie/: {st}")
    for u, i in parse_listing(soup, PORTAL).items():
        add(u, i)
    log(f"  alfabetycznie: {len(meta)} cards")
    # by departments
    soup, st = f.get_soup(PORTAL + "/wedlug-wydzialow/")
    if soup is not None:
        for btn in soup.find_all("button", attrs={"data-target": True}):
            body = soup.find(id=btn["data-target"].lstrip("#"))
            if body is None:
                continue
            dep = norm(btn.get_text())
            for u, i in parse_listing(body, PORTAL).items():
                add(u, i, "departments", dep)
    # categories -> subcategories -> cards
    soup, st = f.get_soup(PORTAL + "/wedlug-kategorii/")
    cat_links = []
    if soup is not None:
        for a in soup.find_all("a", href=re.compile(r"^/[a-z0-9\-]+/$")):
            h = a["href"]
            if h in ("/", "/wedlug-kategorii/", "/alfabetycznie/", "/wedlug-wydzialow/", "/prywatnosc/", "/deklaracja-dostepnosci/"):
                continue
            if (h, norm(a.get_text())) not in cat_links:
                cat_links.append((h, norm(a.get_text())))
    log(f"  categories: {len(cat_links)}")
    for h, name in cat_links:
        s1, st = f.get_soup(PORTAL + h)
        if s1 is None:
            log(f"  category fail {h} {st}")
            continue
        name = name or (norm(s1.find("h1").get_text()) if s1.find("h1") else "") or h.strip("/").replace("-", " ")
        for u, i in parse_listing(s1, PORTAL).items():
            add(u, i, "categories", name)
        subs = []
        for a in s1.find_all("a", href=re.compile("^" + re.escape(h) + r"[^/]+/$")):
            if a["href"] not in [x[0] for x in subs]:
                subs.append((a["href"], norm(a.get_text())))
        for sh, sname in subs:
            s2, st = f.get_soup(PORTAL + sh)
            if s2 is None:
                log(f"  subcategory fail {sh} {st}")
                continue
            sname = (norm(s2.find("h1").get_text()) if s2.find("h1") else "") or sname or sh.strip("/").split("/")[-1].replace("-", " ")
            for u, i in parse_listing(s2, PORTAL).items():
                add(u, i, "categories", f"{name} / {sname}")
    # cards that appear only in category pages are also kept (meta already has them)
    urls = list(meta.keys())
    if max_cards:
        urls = urls[:max_cards]
    log(f"portal: {len(urls)} card URLs")
    cards = []
    for n, u in enumerate(urls, 1):
        soup, st = f.get_soup(u)
        card = parse_card(soup, u, meta[u], st)
        cards.append(card)
        if n % 25 == 0:
            log(f"  card {n}/{len(urls)}")
    return cards


def parse_card(soup, url, m, status):
    c = OrderedDict(
        source="portal", url=url, http_status=status, code=m["code"], title=m["title"],
        departments_index=m["departments"], categories=m["categories"], department_text="",
        online_handling=False, online_reasons=[], external_links=[], attachments=[],
        fees="", last_update="", legal_basis="",
    )
    if soup is None:
        return c
    text = norm(soup.get_text(" "))
    mc = re.search(r"karta nr:?\s*([A-Z]{2,5}\d+)", text)
    if mc:
        c["code"] = mc.group(1)
    h = soup.find("h1")
    if h and norm(h.get_text()):
        c["title"] = norm(h.get_text())
    c["department_text"] = section_text(soup, r"jednostk\w+ odpowiedzialn|gdzie za[lł]atwisz")
    c["fees"] = section_text(soup, r"ile zap[lł]acisz|op[lł]at", 700)
    c["legal_basis"] = section_text(soup, r"podstawa prawna", 600)
    d = DATE_RE.search(text)
    if d:
        c["last_update"] = d.group(1)
    scope = soup.find("div", class_=re.compile("service-card|card-content|content")) or soup
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("mailto:", "tel:", "javascript:", "#")):
            continue
        absu = urljoin(url, href)
        label = norm(a.get_text()) or norm(a.get("title", "")) or (norm(a.img.get("alt", "")) if a.img else "")
        host = urlparse(absu).netloc
        if "/ebokfile/" in absu or ext_of(absu, label) or "attachments/download" in absu:
            if absu not in seen:
                seen.add(absu)
                # context: nearest preceding list item / paragraph text for unlabeled "TUTAJ" links
                ctx = ""
                p = a.find_parent(["li", "p"])
                if p:
                    ctx = norm(p.get_text())[:200]
                c["attachments"].append({"label": label, "context": ctx, "url": absu, "ext": ext_of(absu, label)})
        elif host and not host.endswith("um.bydgoszcz.pl") and EXTERNAL_RE.search(absu):
            if absu not in [e["url"] for e in c["external_links"]] and "/typo3" not in absu:
                c["external_links"].append({"label": label, "url": absu})
    for e in m.get("listing_external", []):
        if e not in [x["url"] for x in c["external_links"]]:
            c["external_links"].append({"label": "listing icon", "url": e})
    reasons = []
    if any("epuap" in e["url"] and "katalog-spraw" in e["url"] for e in c["external_links"]):
        reasons.append("ePUAP catalog link")
    if any(re.search(r"gov\.pl/web|obywatel\.gov|biznes\.gov", e["url"]) for e in c["external_links"]):
        reasons.append("gov.pl / obywatel / biznes link")
    if re.search(r"za[lł]atw sprawę na platformie|przez internet|elektronicznie|online|e-us[lł]ug|ePUAP", text, re.I):
        reasons.append("online keywords in text")
    c["online_handling"] = bool(reasons)
    c["online_reasons"] = reasons
    # explicit denial: "nie można załatwić ... online/przez internet"
    if re.search(r"(nie mo[zż]na|nie jest mo[zż]liwe)[^.]{0,80}(internet|online|elektronicz)", text, re.I):
        c["online_denied_text"] = True
    return c


def crawl_bip(f, log=print):
    pages = OrderedDict()
    queue = [BIP + p for p in BIP_PAGES]
    discovered = []
    done = set()
    while queue and len(done) < 60:
        u = queue.pop(0)
        key = re.sub(r"/artykul/(\d+)/(\d+)?.*", r"/artykul/\1/\2", u)
        if key in done:
            continue
        done.add(key)
        soup, st = f.get_soup(u)
        page = OrderedDict(source="bip", url=u, http_status=st, title="", attachments=[], links_to_other_bip=[])
        if soup is not None:
            h = soup.find("h1") or soup.find("h2")
            page["title"] = norm(h.get_text()) if h else norm(soup.title.get_text() if soup.title else "")
            seen = set()
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                absu = urljoin(u, href)
                label = norm(a.get_text()) or norm(a.get("title", ""))
                if "attachments/download" in absu or ext_of(absu, label) or "/ebokfile/" in absu:
                    if absu not in seen:
                        seen.add(absu)
                        ctx = ""
                        p = a.find_parent(["li", "p", "td", "tr"])
                        if p:
                            ctx = norm(p.get_text())[:200]
                        page["attachments"].append({"label": label, "context": ctx, "url": absu, "ext": ext_of(absu, label)})
                elif "/artykul/" in absu and urlparse(absu).netloc == urlparse(BIP).netloc and BIP_KEYWORDS.search(unquote(absu) + " " + label):
                    page["links_to_other_bip"].append({"label": label, "url": absu})
                    if len(discovered) < 40:
                        discovered.append(absu)
                        queue.append(absu)
        pages[u] = page
        log(f"  bip {u} -> {st}, {len(page['attachments'])} attachments")
    return list(pages.values())


def dedupe_cards(cards):
    """The same card (same code UMBnn) is reachable under several /sprawa/<category-id>/ URLs.
    Merge them: first URL is canonical, the others go to alt_urls; departments/categories are unioned."""
    out = OrderedDict()
    for c in cards:
        k = c.get("code") or c["url"]
        if k not in out:
            c = OrderedDict(c)
            c["alt_urls"] = []
            out[k] = c
            continue
        m = out[k]
        if c["url"] != m["url"] and c["url"] not in m["alt_urls"]:
            m["alt_urls"].append(c["url"])
        for key in ("departments_index", "categories"):
            for v in c.get(key, []):
                if v not in m[key]:
                    m[key].append(v)
        have = {x["url"] for x in m["attachments"]}
        m["attachments"] += [x for x in c["attachments"] if x["url"] not in have]
        have = {x["url"] for x in m["external_links"]}
        m["external_links"] += [x for x in c["external_links"] if x["url"] not in have]
    return list(out.values())


def write_outputs(out, result, cards, bip, log=print):
    with open(os.path.join(out, "forms-catalog.json"), "w", encoding="utf-8", newline="
") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "forms-catalog.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["source", "card_code", "card_title", "department", "card_url", "label", "context", "attachment_url", "ext", "http_status", "content_type", "content_length"])
        for c in cards + bip:
            dep = "; ".join(c.get("departments_index", [])) if c["source"] == "portal" else ""
            for at in c["attachments"]:
                ck = at.get("check") or {}
                w.writerow([c["source"], c.get("code", ""), c.get("title", ""), dep, c["url"], at["label"], at.get("context", ""),
                            at["url"], at["ext"], ck.get("http_status", ""), ck.get("content_type", ""), ck.get("content_length", "")])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
    ap.add_argument("--max-cards", type=int)
    ap.add_argument("--no-head", action="store_true", help="skip HEAD checks of attachments")
    ap.add_argument("--no-bip", action="store_true")
    ap.add_argument("--extra-urls", help="text file with extra URLs to HEAD-check (one per line)")
    ap.add_argument("--postprocess", action="store_true", help="re-read existing forms-catalog.json, dedupe cards by code, rewrite outputs (no network)")
    ap.add_argument("--download", metavar="DIR", help="also save attachment files into DIR (not for the repo)")
    a = ap.parse_args()
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    if a.postprocess:
        p = os.path.join(out, "forms-catalog.json")
        res = json.load(open(p, encoding="utf-8"))
        res["cards_raw_count"] = len(res["cards"])
        res["cards"] = dedupe_cards(res["cards"])
        res["counts"]["cards"] = len(res["cards"])
        write_outputs(out, res, res["cards"], res["bip_pages"])
        print("postprocessed:", res["cards_raw_count"], "->", len(res["cards"]), "cards")
        return
    f = Fetcher()
    t0 = time.time()
    log = lambda s: print(s, flush=True)
    cards_raw = crawl_portal(f, a.max_cards, log)
    cards = dedupe_cards(cards_raw)
    bip = [] if a.no_bip else crawl_bip(f, log)
    extras = []
    if a.extra_urls:
        extras = [l.strip() for l in open(a.extra_urls, encoding="utf-8") if l.strip() and not l.startswith("#")]
    # HEAD checks (each unique URL once)
    uniq = OrderedDict()
    for c in cards + bip:
        for at in c["attachments"]:
            uniq[at["url"]] = None
    for e in extras:
        uniq[e] = None
    log(f"checking {0 if a.no_head else len(uniq)} unique attachment URLs")
    if not a.no_head:
        for i, u in enumerate(list(uniq), 1):
            uniq[u] = f.check_file(u)
            if i % 50 == 0:
                log(f"  head {i}/{len(uniq)}")
    for c in cards + bip:
        for at in c["attachments"]:
            at["check"] = uniq.get(at["url"])
            if not at["ext"] and at["check"] and at["check"].get("content_type"):
                at["ext"] = {"application/pdf": "pdf", "application/msword": "doc",
                             "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
                             "application/rtf": "rtf", "text/rtf": "rtf"}.get(at["check"]["content_type"], "")
    if a.download:
        os.makedirs(a.download, exist_ok=True)
        for u in uniq:
            r, _ = f.request("GET", u)
            if r is not None and r.status_code == 200:
                name = re.sub(r"[^\w.\-]+", "_", unquote(os.path.basename(urlparse(u).path)) or "file")
                with open(os.path.join(a.download, re.sub(r"\W+", "_", urlparse(u).netloc) + "__" + name), "wb") as fh:
                    fh.write(r.content)
    result = OrderedDict(
        generated=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        crawler="tools/crawl_bydgoszcz_forms.py", user_agent=UA, requests_made=f.n,
        duration_s=round(time.time() - t0), robots_rules=f.robots,
        counts=dict(cards=len(cards), bip_pages=len(bip), unique_attachment_urls=len(uniq)),
        cards=cards, bip_pages=bip,
        extra_url_checks=[dict(url=e, **uniq[e]) for e in extras if uniq.get(e)],
    )
    result["cards_raw_count"] = len(cards_raw)
    write_outputs(out, result, cards, bip)
    log(f"done: {len(cards)} cards, {len(bip)} bip pages, {len(uniq)} attachment URLs, {f.n} requests, {round(time.time()-t0)} s")


if __name__ == "__main__":
    main()
