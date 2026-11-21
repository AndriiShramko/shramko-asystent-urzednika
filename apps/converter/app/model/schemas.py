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

ROOT = Path(__file__).resolve().parents[4]
CONTRACTS = ROOT / "contracts" / "coi"
BASE_ID = "https://github.com/AndriiShramko/shramko-asystent-urzednika/contracts/coi/"

SCHEMAS: dict[str, tuple[type[BaseModel], str]] = {
    "page-model": (PageModel, "Page model, output of every reader (design 5.1). Also checked by app.model.page: page "
                              "numbers 1..n, source.pages equals the page count, ids unique in the document, flow "
                              "pages use anchors and native or ocr pages use boxes, table cells name runs of their page."),
    "candidates": (FinderOutput, "Finder output (design 5.2). Also checked by app.model.candidate: ids unique, "
                                 "sections, groups and option marks resolve, a choice_group has two options or more, "
                                 "a comb states its cells."),
    "brief": (Brief, "Brief, output of the understanding step (design 5.3). Also checked by app.model.brief: status "
                     "stated or ambiguous has evidence and not_found has none, field keys and roles unique, conditions "
                     "name existing fields and options, a required field states its basis."),
    "meta": (Meta, "Sidecar meta keyed by form ids (design 5.4). Also checked by app.model.meta: the ledger closes "
                   "(blanks_found equals the sum of the five fates, one row per blank, counts equal rows by fate), "
                   "coverage adds up, decisions resolve existing warnings."),
}


class _NoNull(GenerateJsonSchema):
    """Optional means absent, never null."""

    def nullable_schema(self, schema: Any) -> Any:
        return self.generate_inner(schema["schema"])

    def default_schema(self, schema: Any) -> Any:
        out = super().default_schema(schema)
        if isinstance(out, dict) and out.get("default", 0) is None:
            out.pop("default")
        return out


def schema_for(name: str) -> dict[str, Any]:
    model, description = SCHEMAS[name]
    body = model.model_json_schema(schema_generator=_NoNull, by_alias=True)
    body["description"] = description
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": BASE_ID + f"{name}.schema.json", **body}


def main(argv: list[str]) -> int:
    check = "--check" in argv
    differ = []
    for name in SCHEMAS:
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
    print("schemas", "match" if check else "written", len(SCHEMAS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
