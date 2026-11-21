"""Print file, line number and hit kind (never the value) for the given files, using the owner's scanner."""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("coop", str(Path.home() / ".claude" / "coop" / "coop.py"))
coop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coop)

for name in sys.argv[1:]:
    above = []
    code = bool(coop.CODE_FILE.search(name))
    for n, line in enumerate(Path(name).read_text(encoding="utf-8", errors="replace").split("\n"), 1):
        line = line.rstrip("\r")
        found = coop.value_hits(line) + coop.secret_hits(line, code, "\n".join(above), frozenset())
        above = (above + [line])[-3:]
        for kind, value in found:
            print("%s:%d %s#%s len=%d" % (name, n, kind, coop.digest(value)[:6], len(value)))
print("done")
