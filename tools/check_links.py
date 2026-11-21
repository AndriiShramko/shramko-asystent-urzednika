#!/usr/bin/env python3
"""Check that every relative link in the Markdown files of the repository points to an existing file.

Usage: python tools/check_links.py [repo_root]
Exit code 0 when all links resolve, 1 otherwise. External links (http, https, mailto) are not fetched.
"""
import glob
import os
import re
import sys

SKIP_DIRS = ("node_modules", ".worktrees", ".git", "data/forms-cache")
LINK = re.compile(r"\]\(([^)#\s]+)(#[^)]*)?\)")


def main() -> int:
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    bad = []
    for path in glob.glob(os.path.join(root, "**", "*.md"), recursive=True):
        rel = os.path.relpath(path, root).replace(os.sep, "/")
        if any(rel.startswith(d + "/") or ("/" + d + "/") in ("/" + rel) for d in SKIP_DIRS):
            continue
        if rel.startswith("research/_jobs/"):
            continue
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        # links inside fenced code blocks are examples, not links
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for match in LINK.finditer(text):
            target = match.group(1)
            if re.match(r"^(https?:|mailto:|tel:)", target):
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                bad.append((rel, target))
    for rel, target in bad:
        print(f"BROKEN {rel} -> {target}")
    print(f"checked; broken links: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
