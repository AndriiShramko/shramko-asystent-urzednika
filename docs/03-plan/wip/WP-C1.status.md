# WP-C1 REQUIRED and optional follow the paper's own words: status

Claimed by: build7 (agent c1-required); heartbeat: 2026-11-22 00:55; state: running
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
- [x] (c) negation guard before a required cue (`_says_required` in `_fields.py`), tests `tests/mean/test_mean_c1_negation.py`
- [x] (d) optional wording: `ewentualn`, "jeśli/jeżeli (są) różn", "w razie potrzeby", "niewymagan", "nie jest/są wymagan|obowiązkow"
      (habit row `optional_wording`, `_says_optional` in `_fields.py`), tests `tests/mean/test_mean_c1_optional.py`;
      with the mean tests and `tests/validators/test_required.py`: 104 passed
- [x] (e) required and optional cues read from the field's hint and the title of its own section (`_aside_says_required`,
      `_field` in `_fields.py`), tests `tests/mean/test_mean_c1_sources.py`;
      `bash tools/gate.sh py -m pytest apps/converter/tests/mean apps/converter/tests/validators/test_required.py -q` = 122 passed, 1 skipped
- [ ] (e2) item 4 of the order: cues "należy wypełnić" (no word after it) and "musi zawierać" in a habit row `required_wording`,
      read by `_says_required`; tests first (`tests/mean/test_mean_c1_wording.py`)
- [ ] (f) counts after, list of changed fields here
- [ ] (g) fast gate, chain compare, state `ready_to_merge`
- [ ] (h) only if (c) to (e) are green: legend "pola oznaczone * / gwiazdką są obowiązkowe" makes starred labels required

## Decisions
- Negation: the word "nie", "niedotyczy", or "nie" glued to the cue, within 40 characters BEFORE a required cue, blocks it /
  the order's item 3, testable / rules out reading a negation after the cue; a glued "...nie" of a footnote blocks too (honest gap).
- New wording goes into NEW habit rows (`optional_wording`, `required_wording`) read only by `_fields.py`, not into the row
  `optional` / `_doc.clean_label` (not owned) would then swallow a bracket like "(jeśli różni się od ...)" as the mark and
  the hint would vanish from the form / rules out a change of the composer's reading of `optional`.
- Section title: an optional wording counts anywhere in the title; a required cue counts only inside a bracket of the title
  ("(pola obowiązkowe)") / a running title like "Wymagane załączniki" must not make every field required / rules out plain-title cues.
- In a hint or a title bracket a required cue next to a conditional word (habit `conditional`) is no cue / "wymagane w przypadku ..."
  is a condition, not "required" / such a field stays "inferred" (not written under REQUIRED_POLICY=paper).
- The field's own words (label, hint, footnote) outrank the section title; optional outranks required among own words (as before).
- "należy wypełnić" is a cue only when no word follows it ("należy wypełnić drukowanymi literami" tells how, not whether).

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|

## Negative control
On the unpatched code (be69fa0, main's `_fields.py`) the three new test files gave "20 failed, 9 passed": every case that
asserts new behaviour failed (for example `test_a_negated_cue_is_not_required_by_the_paper[Kolor furtki nie jest wymagany]`:
basis was "paper"); the 9 that passed are the guards that must hold before and after. With the guard of step c:
`bash tools/gate.sh py -m pytest apps/converter/tests/mean/test_mean_c1_negation.py ... test_mean_core.py test_mean_f3b.py test_mean_f3c.py -q` = 79 passed.

## Left for the next stage
Steps (f), (g), then (e2) and (h) if time is left. Heartbeat of this section: 2026-11-22 01:00. Steps (c), (d), (e) are
committed and their tests pass (122 passed on the commit of step e). NEXT: (f) run the two measuring commands below (4 and the
dump tool, once for sets 08 and 09 and once without set names for all sets), diff against the before files, write the changed
fields into "## Evidence"; gate of the order: no field loses the basis "paper", items 20 and 29 of set 09 optional in doc, docx, pdf.
`field_of(label, title=..., footnote=...)` of `test_mean_c1_negation.py` builds a synthetic one-field paper for new tests.
Before-dump of ALL sets on main's code: `tmp/c1-brief-all-before.tsv` = 689 fields, 670 required, 10 with basis paper
(local, not in git: re-make it from a checkout of `main` with the same tool if needed). Measuring tool of this package:
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
