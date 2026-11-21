"""The three corpora. A corpus item is (corpus, key, path, name): `key` is a hash (hostile: the built name) and never
the name of a file of the sets or the archive."""
from __future__ import annotations

import hashlib
import json
import random
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SAMPLE = HERE / "sample.json"
ARCHIVE_DIR = ROOT / "data" / "archive"
FORMATS = ("pdf", "doc", "docx", "odt", "ods", "xls", "xlsx", "jpg", "jpeg", "png")
PER_FORMAT = 15
MIN_TOTAL = 80
SEED = 20261121


@dataclass(frozen=True)
class Item:
    corpus: str
    key: str
    path: Path
    name: str
    fmt: str


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def fmt_of(name: str) -> str:
    return Path(name).suffix.lower().lstrip(".") or "none"


def sets_items() -> list[Item]:
    from tools.coi_paths import sets

    out = []
    for folder in sets():
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.suffix.lower() in {"." + f for f in (*FORMATS, "jpe")}:
                out.append(Item("sets", sha256_of(p)[:16], p, p.name, fmt_of(p.name)))
    return out


def build_sample(archive: Path = ARCHIVE_DIR, seed: int = SEED, per_format: int = PER_FORMAT) -> dict:
    """Seeded choice per format from the files of `archive`; the result lists hashes only."""
    by_fmt: dict[str, list[tuple[str, Path]]] = {}
    for p in sorted(archive.rglob("*")):
        if p.is_file() and fmt_of(p.name) in FORMATS:
            by_fmt.setdefault(fmt_of(p.name), []).append((sha256_of(p), p))
    rng = random.Random(seed)
    files = []
    for fmt in FORMATS:
        pool = sorted({h: p for h, p in by_fmt.get(fmt, [])}.items())  # unique contents, order fixed by hash
        for h, p in rng.sample(pool, min(per_format, len(pool))):
            files.append({"format": fmt, "sha256": h, "size": p.stat().st_size,
                          "name_hash": hashlib.sha256(p.name.encode("utf-8")).hexdigest()[:16]})
    files.sort(key=lambda r: (r["format"], r["sha256"]))
    return {"seed": seed, "per_format": per_format, "archive_files": sum(len(v) for v in by_fmt.values()),
            "total": len(files), "files": files}


def unseen_items(archive: Path = ARCHIVE_DIR, sample: Path = SAMPLE) -> list[Item]:
    spec = json.loads(sample.read_text(encoding="utf-8"))
    wanted = {f["sha256"]: f for f in spec["files"]}
    sizes = {f["size"] for f in wanted.values()}
    found: dict[str, Path] = {}
    for p in sorted(archive.rglob("*")):
        if p.is_file() and p.stat().st_size in sizes:
            h = sha256_of(p)
            if h in wanted and h not in found:
                found[h] = p
    missing = len(wanted) - len(found)
    if missing:
        raise FileNotFoundError(f"{missing} of {len(wanted)} files of the sample are not in {archive.name}/")
    return [Item("unseen", h[:16], found[h], "sample-" + h[:8] + "." + wanted[h]["format"], wanted[h]["format"])
            for h in sorted(wanted)]


def hostile_items(folder: Path | None = None) -> list[Item]:
    from eval.chain import hostile

    folder = folder or Path(tempfile.mkdtemp(prefix="chain-hostile-"))
    return [Item("hostile", name, p, name, fmt_of(name)) for name, p in sorted(hostile.build(folder).items())]
