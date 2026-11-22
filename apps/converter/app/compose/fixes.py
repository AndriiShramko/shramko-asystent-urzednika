"""The ready fix of a remark (W11 CLERK-S; contract: sidecar `warnings[].fix`, model `app.model.sidecar.Fix`).

A remark that only says "check this" makes the official type. Every remark the converter can answer therefore
carries a `fix`:
  applied  the converter decided itself and only tells what it did; such a remark is not shown to the official;
  choice   2 to 5 ready options, the most likely first; exactly one is `current` (the state the form JSON has now);
  input    nothing could be proposed: the official types the value.
The composer writes a HINT (`Remark.fix`): the same object, but with places named by meaning, because ids and
positions exist only after the form is written. `resolve` turns a hint into the final object:
  hint["target"]                the meaning path of one node ("dane/adresat/nazwa"), or a brief key ("brief:<key>")
  option["props"]               {property: value} written on the target
  option["fields"]              {brief key: {property: value}} written on several fields of the matter
  input["props"]                [property, ...] of the target that take the typed string
The property "REQUIRED" is not a key of the form: True or False adds or removes REQUIRED in the node's `validation`
list and keeps the other validators. A `set` replaces one value and never changes the shape of the form, so the
pointers of the other fixes stay valid after any pick.
"""
from __future__ import annotations

from typing import Any, Mapping

from app import lexicon

_USUALLY_OPTIONAL = lexicon.regex("habits", habit="usually_optional")

__all__ = ["attach", "brief_hints", "index", "paper", "resolve", "rule_source", "seen_by_clerk"]


def paper(evidence: Any) -> dict[str, Any]:
    """Source "paper" from an Evidence of the brief (page, box, anchor, quote)."""
    d = evidence.model_dump(mode="json", exclude_none=True) if hasattr(evidence, "model_dump") else dict(evidence or {})
    return {"type": "paper", **{k: d[k] for k in ("page", "box", "anchor", "quote") if d.get(k) not in (None, [], "")}}


def rule_source(name: str) -> dict[str, str]:
    return {"type": "rule", "name": name}


def index(form: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Form id -> {"pointer", "node", "tab"} for every section and every component."""
    out: dict[str, dict[str, Any]] = {}
    for ti, tab in enumerate(form.get("tabs", [])):
        for qi, q in enumerate(tab.get("questions", [])):
            sec = q["field"]
            base = f"/tabs/{ti}/questions/{qi}/field"
            out[sec["id"]] = {"pointer": base, "node": sec, "tab": tab.get("title", "")}
            for ci, cell in enumerate(sec.get("repeatingSectionGrid", [])):
                out[cell["field"]["id"]] = {"pointer": f"{base}/repeatingSectionGrid/{ci}/field", "node": cell["field"],
                                            "tab": tab.get("title", "")}
    return out


def _sets(place: Mapping[str, Any], props: Mapping[str, Any]) -> list[dict[str, Any]]:
    out = []
    for prop, value in props.items():
        if prop == "REQUIRED":
            rest = [v for v in place["node"].get("validation", []) if v != "REQUIRED"]
            out.append({"pointer": f"{place['pointer']}/validation", "value": (["REQUIRED"] if value else []) + rest})
        else:
            out.append({"pointer": f"{place['pointer']}/{prop}", "value": value})
    return out


def resolve(hint: Mapping[str, Any], nodes: Mapping[str, dict[str, Any]], by_path: Mapping[str, str],
            by_key: Mapping[str, str]) -> dict[str, Any] | None:
    """The final `fix` of one hint; None when a place it names is not in the form (the remark then stays as it was)."""
    def place_of(name: str | None) -> dict[str, Any] | None:
        if name is None:
            return None
        fid = by_key.get(name[6:]) if name.startswith("brief:") else by_path.get(name)
        return nodes.get(fid or "")

    place = place_of(hint.get("target"))
    if hint.get("target") is not None and place is None:
        return None
    fix: dict[str, Any] = {"kind": hint["kind"], "rule": hint["rule"], "text": hint["text"]}
    if place is not None:
        fix["target"] = {"id": place["node"]["id"], "pointer": place["pointer"], "label": place["node"].get("title", ""),
                         "tab": place["tab"]}
    if hint.get("value") is not None:
        fix["value"] = hint["value"]
    options = []
    for o in hint.get("options", ()):
        sets: list[dict[str, Any]] = _sets(place, o["props"]) if place is not None and o.get("props") else []
        for key, props in (o.get("fields") or {}).items():
            there = place_of(f"brief:{key}")
            if there is None:
                return None
            sets += _sets(there, props)
        options.append({"label": o["label"], "value": o["value"], "current": bool(o.get("current")), "set": sets,
                        **({"source": o["source"]} if o.get("source") else {})})
    if options:
        if sum(o["current"] for o in options) != 1 or not 2 <= len(options) <= 5:
            return None
        fix["options"] = options
    if hint.get("input") and place is not None:
        fixed = _sets(place, hint["input"].get("fixed") or {})
        fix["input"] = {"label": hint["input"]["label"],
                        "set": [{"pointer": f"{place['pointer']}/{prop}", "from": "input"} for prop in hint["input"]["props"]] + fixed}
    if hint.get("source"):
        fix["source"] = hint["source"]
    if fix["kind"] == "choice" and "options" not in fix or fix["kind"] == "input" and "input" not in fix:
        return None
    return fix


def attach(form: Mapping[str, Any], warnings: list[dict[str, Any]], hints: Mapping[int, Mapping[str, Any]],
           paths: Mapping[str, str], brief_keys: Mapping[str, str]) -> list[dict[str, Any]]:
    """`warnings` with `fix` written on the entries `hints` names by position. A hint that does not resolve, or any
    slip, leaves the remark exactly as it was: a fix is a courtesy and never costs the report."""
    try:
        nodes = index(form)
        by_path = {key.split("/", 1)[1]: fid for fid, key in paths.items() if "/" in key}
        by_key = {key: fid for fid, key in brief_keys.items()}
    except Exception:  # noqa: BLE001
        return warnings
    out = list(warnings)
    for i, hint in hints.items():
        try:
            fix = resolve(hint, nodes, by_path, by_key)
        except Exception:  # noqa: BLE001
            fix = None
        if fix is not None:
            out[i] = {**out[i], "fix": fix}
    return out


def brief_hints(warnings: list[dict[str, Any]], brief: Any) -> dict[int, dict[str, Any]]:
    """Hints for the warnings of the understanding step that name one field of the brief. REQUIRED_INFERRED of one
    field (written only under the required policy "inferred"): the rule "a blank the paper does not mark optional
    is required" decided, so the remark only tells; when the label names what the partner's own exports leave
    optional (telephone, e-mail, flat number, remarks) the official gets the two answers by a click."""
    try:
        fields = {f.key: f for m in brief.matter for f in m.fields if f.key}
    except Exception:  # noqa: BLE001
        return {}
    out: dict[int, dict[str, Any]] = {}
    for i, w in enumerate(warnings):
        f = fields.get(w.get("field") or "")
        if w.get("code") != "REQUIRED_INFERRED" or f is None:
            continue
        target, label = f"brief:{f.key}", f.label[:80]
        if _USUALLY_OPTIONAL.search(f.label):
            out[i] = {"kind": "choice", "rule": "required.usually_optional", "target": target,
                      "text": f"Druk nie mówi, czy pole „{label}” jest obowiązkowe.",
                      "options": [{"label": "Obowiązkowe", "value": "required", "current": True, "props": {"REQUIRED": True},
                                   "source": rule_source("unmarked-blank-is-required")},
                                  {"label": "Nieobowiązkowe", "value": "optional", "current": False, "props": {"REQUIRED": False},
                                   "source": {"type": "dictionary", "name": "usually-optional"}}]}
        else:
            out[i] = {"kind": "applied", "rule": "required.unmarked_blank", "target": target, "value": "required",
                      "text": f"Pole „{label}” oznaczono jako obowiązkowe: druk nie mówi, że można je pominąć.",
                      "source": rule_source("unmarked-blank-is-required")}
    return out


def seen_by_clerk(warning: Mapping[str, Any]) -> bool:
    """The rule of the official's list: everything except what the converter applied itself."""
    return (warning.get("fix") or {}).get("kind") != "applied"
