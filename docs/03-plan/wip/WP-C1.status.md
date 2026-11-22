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
- [x] (e2) item 4 of the order: cues "należy wypełnić" (no word after it) and "musi zawierać" in a habit row `required_wording`,
      read by `_says_required`; tests `tests/mean/test_mean_c1_wording.py` (4 of 8 failed before the code);
      mean tests and `test_required.py`: 130 passed, 1 skipped. The fast gate and the dump are NOT yet re-run on this code.
- [x] (f) counts after: brief dump (28 fields changed, all "required, inferred" -> optional) and form counts over all
      70 inputs (`count_sets.py --diff`: no line, so no validator and no REQUIRED of a form changed; inputs equal) in "## Evidence"
- [ ] (g) fast gate, chain compare, state `ready_to_merge`
- [x] (h) legend "pola oznaczone * / gwiazdką są obowiązkowe": needs NO product code. The legend is the footnote of the star,
      and the footnote path already carries it: starred label "paper", the unstarred one "inferred", the star of "niepotrzebne
      skreślić" no cue, a negated legend optional (new with the guard). Pinned in `tests/mean/test_mean_c1_legend.py`: 5 passed.
      Limit: it holds only where the finder attaches the star to the label as a footnote mark and reads the legend as a note
      (`app/find/**`, not owned); a legend printed in the head or the body of the paper is not read.

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
| Set 09: items 20 and 29 optional in doc, docx, pdf | `dump_required.py tmp/c1-brief-all-after.tsv`, diff against the run on main's code | in each of doc, docx, pdf: "Adres do korespondencji" (hint "jeśli różni się od ...") x3 and "Ewentualne dodatkowe informacje ..." x3 went from "required, inferred" to optional (18 fields) | 6d5e675 |
| Set 08: matter fields not above the paper-cued ones | same | ods and xlsx: "Nr tel./fax" and four consent rows of the section titled "... (pola nieobowiązkowe)" went to optional (10 fields); no field gained REQUIRED | 6d5e675 |
| A field REQUIRED by the paper stays so | same, all sets, 5 text formats | 689 fields; basis "paper" 10 before, 10 after; 0 changed lines held "paper"; required 670 -> 642; the 28 changed fields are exactly the two rows above, no other set changed | 6d5e675 |
| No judged set loses an element or a validator in any format | `count_sets.py tmp/c1-after.json --all`, then `--diff tmp/c1-before.json tmp/c1-after.json` | 70 inputs (every set, every format): `--diff` prints nothing; inputs and REQUIRED per form equal; only "required in the brief" drops: set 08 ods and xlsx 105 -> 100, set 09 doc 51 -> 45, docx 44 -> 38, pdf 62 -> 56 (sum 28) | 6d5e675 |
| Fast gate | `bash tools/gate.sh fast > tmp/fast.log 2>&1` | "gate: fast PASSED on d0d7bc6": 870 passed, 3 skipped, 22 deselected; then 21 passed | d0d7bc6 |
| Unit tests | `bash tools/gate.sh py -m pytest apps/converter/tests/mean apps/converter/tests/validators/test_required.py -q` | 122 passed, 1 skipped (29 new cases in three files) | 6d5e675 |

## Negative control
On the unpatched code (be69fa0, main's `_fields.py`) the three new test files gave "20 failed, 9 passed": every case that
asserts new behaviour failed (for example `test_a_negated_cue_is_not_required_by_the_paper[Kolor furtki nie jest wymagany]`:
basis was "paper"); the 9 that passed are the guards that must hold before and after. With the guard of step c:
`bash tools/gate.sh py -m pytest apps/converter/tests/mean/test_mean_c1_negation.py ... test_mean_core.py test_mean_f3b.py test_mean_f3c.py -q` = 79 passed.

## Left for the next stage
The chain compare of (g), then (e2) and (h) if time is left. Heartbeat of this section: 2026-11-22 01:30. Steps (c) to (f)
are committed; the fast gate PASSED on d0d7bc6 (code equal to 6d5e675). NEXT: the chain compare of command 5 below (read the
tail of `tmp/chain.log`; then `git checkout eval/chain/summary.json`), write the result into "## Evidence", set the state in
line 3 to `ready_to_merge`. `main` has two newer commits (STATUS and results, documents only): `git merge --no-edit main` before
the hand-over. The package is mergeable without (e2) and (h): they only add cues, and no field of any set holds the words of (e2)
(0 of 689 fields have "należy wypełnić" or "musi zawierać" in label, hint or section title).
Heartbeat 01:45: `main` (with WP-H4) is merged into the branch (4f33bbb); the three checks below were STARTED on that code in
one background command and their result is not yet written here: if this line is still the last word, run them again.
(e2) is committed after that gate run (heartbeat 01:35): so RE-RUN on the head of the branch, in this order: the dump tool
without set names (expect `diff tmp/c1-brief-all-after.tsv` = no line), the chain compare, the fast gate. If one of them is red
and time is short, `git revert --no-edit <commit of e2>` returns the code that passed everything above.
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
