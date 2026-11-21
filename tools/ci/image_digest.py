#!/usr/bin/env python3
"""Print the digest of the published image for a commit hash, anonymously (WP-F20, build-time tool).

    python tools/ci/image_digest.py COMMIT [--target core|plus] [--tag TAG]

Asks ghcr.io for the manifest of the tag `<commit>` (core) or `<commit>-plus` (plus) with an anonymous pull token
(no credential of ours is used or needed: the package is public). Prints `ghcr.io/...@sha256:...`; exit 1 when
the tag does not exist or is not public. `--tag` names a tag directly (latest-main, latest-main-plus).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

REGISTRY = "ghcr.io"
REPO = "andriishramko/shramko-asystent-urzednika"
ACCEPT = ", ".join(["application/vnd.oci.image.index.v1+json", "application/vnd.oci.image.manifest.v1+json",
                    "application/vnd.docker.distribution.manifest.list.v2+json",
                    "application/vnd.docker.distribution.manifest.v2+json"])


def tag_for(commit: str, target: str) -> str:
    return commit if target == "core" else f"{commit}-{target}"


def digest(tag: str) -> str:
    url = f"https://{REGISTRY}/token?service={REGISTRY}&scope=repository:{REPO}:pull"
    with urllib.request.urlopen(url, timeout=30) as r:
        bearer = json.load(r)["token"]
    req = urllib.request.Request(f"https://{REGISTRY}/v2/{REPO}/manifests/{tag}", method="HEAD",
                                 headers={"Authorization": f"Bearer {bearer}", "Accept": ACCEPT})
    with urllib.request.urlopen(req, timeout=30) as r:
        value = r.headers["Docker-Content-Digest"]
    if not value or not value.startswith("sha256:"):
        raise ValueError("no digest in the answer")
    return f"{REGISTRY}/{REPO}@{value}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("commit", nargs="?")
    ap.add_argument("--target", default="core", choices=["core", "plus"])
    ap.add_argument("--tag")
    args = ap.parse_args(argv)
    if not (args.commit or args.tag):
        ap.error("a commit hash or --tag is required")
    tag = args.tag or tag_for(args.commit, args.target)
    try:
        print(digest(tag))
    except (urllib.error.URLError, ValueError, KeyError) as exc:
        print(f"no anonymous manifest for tag {tag}: {type(exc).__name__} {getattr(exc, 'code', '')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
