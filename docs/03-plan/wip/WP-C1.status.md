# WP-C1 REQUIRED and optional follow the paper's own words: status

Claimed by: build7 (agent c1-required); heartbeat: 2026-11-22 00:47; state: running
Branch: wp/C1-required-cues (cut from main 7fedaed)   Stage now: core

Owned paths: `apps/converter/app/mean/_fields.py`, `apps/converter/app/lexicon/habits.json`,
`apps/converter/tests/mean/**`, this file. Python is only `bash tools/gate.sh py ...`.

## Status
- [x] (a) status file
- [x] (b) counts before on main 7fedaed (`tmp/c1-before.json` with `--all`, `tmp/c1-brief-before.tsv`; not committed).
      Form REQUIRED (policy paper): judged-08 0 in all 8 formats; judged-09 doc 2, docx 3, pdf 3, ods 2, xlsx 2.
      Brief of sets 08 and 09 (`dump_required.py`, 5 text formats): 479 fields, 468 required, 0 with basis paper.
      Targets seen in the brief, all "required, inferred" today: set 09 "Adres do korespondencji" with the hint
      "jeśli różni się od ..." (doc, docx, pdf) and "Ewentualne dodatkowe informacje ..." (doc, docx, pdf);
      set 08 ods/xlsx: fields of the section titled "... (pola nieobowiązkowe)" ("Nr tel./fax", the consent rows).
      NOTE: `count_sets.py` takes OUT.json as its FIRST argument: `count_sets.py tmp/x.json --all`.
- [ ] (c) negation guard before a required cue, tests in `apps/converter/tests/mean/test_mean_c1.py`
- [ ] (d) optional habits: `ewentualn`, "jeśli/jeżeli (są) różni", "w razie potrzeby", tests
- [ ] (e) required and optional cues read from the field's hint and the title of its own section, tests
- [ ] (f) counts after, list of changed fields here
- [ ] (g) fast gate, chain compare, state `ready_to_merge`
- [ ] (h) only if (c) to (e) are green: legend "pola oznaczone * / gwiazdką są obowiązkowe" makes starred labels required

## Decisions
- (none yet)

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control
(to record in step c: a new test that fails on the unpatched code)

## Left for the next stage
Everything from (c) on. Heartbeat of this section: 2026-11-22 00:56. Measuring tool of this package:
`bash tools/gate.sh py apps/converter/tests/mean/dump_required.py tmp/c1-brief-after.tsv judged-08 judged-09`
(about 1 minute; diff it against a run on main to list the changed fields). Facts found so far (no code changed yet):
- `apps/converter/app/mean/_fields.py` lines 561 to 571: `optional = optional or OPTIONAL.search(low) or notes`,
  `marked = REQUIRED.search(low) or notes`, `required = not optional`, `basis = "paper" if marked else "inferred"`.
- `OPTIONAL` and `REQUIRED` are compiled in `apps/converter/app/mean/_doc.py` (NOT owned) from the rows `optional`
  and `required` of `apps/converter/app/lexicon/habits.json` (owned). Their patterns hold no spaces on purpose
  (footnotes are matched with whitespace removed), so a new phrase is written with `\s*` between its words.
- The habit `optional` is also read by `app/compose/required.py` (label, hint, section title): a wider pattern widens it there too.
- `_NOT_REQUIRED` at line 57 of `_fields.py` already holds the negation wording of either-or attachments; reuse its idea.
Exact next commands (from the worktree root):
1. (done) `mkdir -p tmp && bash tools/gate.sh py apps/converter/tests/validators/count_sets.py tmp/c1-before.json --all`
2. write `apps/converter/tests/mean/test_mean_c1.py` (look at `test_mean_core.py` for how a brief is built from synthetic candidates)
3. `bash tools/gate.sh py -m pytest apps/converter/tests/mean -q`
4. after the code: `bash tools/gate.sh py apps/converter/tests/validators/count_sets.py tmp/c1-after.json`, then `--diff tmp/c1-before.json tmp/c1-after.json`
5. `bash tools/gate.sh fast > tmp/fast.log 2>&1`; `bash tools/gate.sh py -m eval.chain --compare --archive C:/dev/shramko-asystent-urzednika/data/archive > tmp/chain.log 2>&1`; then `git checkout eval/chain/summary.json`
After every commit: `git branch -f wp/C1-required-cues HEAD && git push origin wp/C1-required-cues`.
Checks that passed: none yet.

## Requests to lead
- (none)

## Cost notes
- (none yet)
