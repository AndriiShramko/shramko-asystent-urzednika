"""Write (or check) the JSON Schema files of our own contracts from the models.

    python -m app.model.schemas           rewrite contracts/coi/{page-model,candidates,brief,meta}.schema.json
    python -m app.model.schemas --check   exit 1 when a file differs from the models

Draft 2020-12. Optional keys are not nullable: our contracts leave a key out instead of writing null.
Rules a schema cannot express (ledger closes, references resolve, box or anchor by page origin) are checked
by the models and named in each schema's description.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema

from .brief import Brief
from .candidate import FinderOutput
from .common import canonical_json
from .meta import Meta
from .page import PageModel
from .sidecar import Sidecar

ROOT = Path(__file__).resolve().parents[4]
CONTRACTS = ROOT / "contracts" / "coi"
BASE_ID = "https://github.com/AndriiShramko/shramko-asystent-urzednika/contracts/coi/"

SCHEMAS: dict[str, tuple[type[BaseModel], str]] = {
    "page-model": (PageModel, "Page model, output of every reader (design 5.1). Also checked by app.model.page: page "
                              "numbers 1..n, source.pages equals the page count, ids unique in the document, every "
                              "element of a flow page has an anchor and of a native or ocr page a box (1.1: the other "
                              "may be given too), a flow page carries lines, rects or pictures only with its size, "
                              "table cells name runs of their page. Revision 1.1, additive."),
    "candidates": (FinderOutput, "Finder output (design 5.2). Also checked by app.model.candidate: ids unique, "
                                 "sections, groups and option marks resolve, a choice_group has two options or more, "
                                 "a comb states its cells; spans lie inside their runs (check_spans against the page "
                                 "model). Revision 1.1, additive."),
    "brief": (Brief, "Brief, output of the understanding step (design 5.3). Also checked by app.model.brief: status "
                     "stated or ambiguous has a quote and not_found has no evidence, field keys and roles unique, "
                     "conditions name existing fields and options (1.1: or the applicant selector and its option "
                     "keys), a required field states its basis, dispositions name each candidate once and resolve. "
                     "Revision 1.1, additive."),
    "meta": (Meta, "Sidecar meta keyed by form ids (design 5.4). Also checked by app.model.meta: the ledger closes "
                   "(blanks_found equals the sum of the five fates, one row per blank, counts equal rows by fate), "
                   "coverage adds up, decisions resolve existing warnings; app.model.ledger assembles the ledger "
                   "from the finder's candidates and the brief's dispositions. Revision 1.1, additive."),
}

# A8 VB-1: the sidecar a run returns today (app.pipeline.run); kept apart from SCHEMAS, which pairs each contract
# with an example of the design. `meta` above stays the design 5.4 target.
RUN_SCHEMAS: dict[str, tuple[type[BaseModel], str]] = {
    "sidecar": (Sidecar, "Sidecar returned by a run today (app.pipeline.run: the meta of /v1/convert, results/*/meta.json). "
                         "Not meta.schema.json, the design 5.4 target that no run writes yet. Also checked by "
                         "app.model.meta.Ledger: the ledger closes. Warning codes are app.model.common.WarningCode."),
}


class _NoNull(GenerateJsonSchema):
    """Optional means absent, never null."""

    def nullable_schema(self, schema: Any) -> Any:
        return self.generate_inner(schema["schema"])

    def default_schema(self, schema: Any) -> Any:
        out = super().default_schema(schema)
        if isinstance(out, dict) and out.get("default", 0) is None:
            out.pop("default")
        if isinstance(out, dict) and isinstance(out.get("default"), dict):  # a default object leaves its absent keys out
            out["default"] = {k: v for k, v in out["default"].items() if v is not None}
        return out


def schema_for(name: str) -> dict[str, Any]:
    model, description = {**SCHEMAS, **RUN_SCHEMAS}[name]
    body = model.model_json_schema(schema_generator=_NoNull, by_alias=True)
    body["description"] = description
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE_ID + f"{name}.schema.json", **body}


def main(argv: list[str]) -> int:
    check = "--check" in argv
    differ = []
    for name in (*SCHEMAS, *RUN_SCHEMAS):
        path = CONTRACTS / f"{name}.schema.json"
        data = canonical_json(schema_for(name))
        if check:
            if not path.is_file() or path.read_bytes() != data:
                differ.append(path.name)
        else:
            path.write_bytes(data)
    if differ:
        print("schemas differ from the models:", ", ".join(differ), "- run: python -m app.model.schemas")
        return 1
    print("schemas", "match" if check else "written", len(SCHEMAS) + len(RUN_SCHEMAS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
