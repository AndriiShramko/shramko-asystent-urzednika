"""Replace the block of STATUS.md from the line starting with '**Running (' up to (not including) the line
starting with '**For the owner' by the text of a file; set the 'Last update' time. Lead's scratch tool.

    python status_block.py STATUS.md BLOCK.md HH:MM
"""
import re
import sys
from pathlib import Path

status, block, hhmm = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
lines = status.read_text(encoding="utf-8").split("\n")
start = next(i for i, x in enumerate(lines) if x.startswith("**Running ("))
end = next(i for i, x in enumerate(lines) if i > start and x.startswith("**For the owner"))
new = block.read_text(encoding="utf-8").replace("HH:MM", hhmm).rstrip("\n").split("\n")
lines[start:end] = new + [""]
text = "\n".join(lines)
text = re.sub(r"^Last update: 2026-11-21 \d\d:\d\d CET\.", "Last update: 2026-11-21 %s CET." % hhmm, text, count=1, flags=re.M)
status.write_text(text, encoding="utf-8", newline="\n")
print("status block replaced: %d lines, time %s" % (len(new), hhmm))
