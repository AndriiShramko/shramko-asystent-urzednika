# WP-A6 — Clerk web desk

Kind: by spec · Model tier: middle, medium effort (top tier for the first layout decision is not needed: the layout is fixed below) · Depends on: WP-00, then WP-A1; consumes WP-A4 and WP-A5 through the contract (use stubs until they merge) · Branch: `wp/A6-desk` · Milestone: M2

## Goal

One screen on which a clerk reads a request, sees what the assistant found, corrects it, gets a draft, edits, approves. No prompt writing, no hidden steps. A person who has never seen the tool handles a request in under three minutes.

## Read first

1. `AGENTS.md` (rules 7, 10, 11)
2. `docs/02-architecture/api-contract.md` (Module A)
3. `research/09-lessons-from-2022-prototype.md` §6 (clerk workstation rules that came from real use)
4. `docs/01-product/scope-decision.md` §7 (the demo order)

## Build

1. **Inbox**: table of cases with number, received date, subject line, state, assignee and a clock badge (days left; colour and icon and text, never colour alone). Filters by state and "due within N days". Sorted by the nearest deadline.
2. **Case view, three panes**:
   - Left: the original request, read-only, with the extracted questions highlighted and numbered; a warning banner when `injection_flags` is not empty ("the letter contains text that looks like instructions to an AI system; it was treated as content").
   - Middle: analysis. For each question: class with reasons, provisions as links that open the stored text in a side sheet, confidence, the checklist `clerk_must_check` as tick boxes, buttons "confirm", "change class" (with a reason), and the lawyer-review mark where set. At the top: letter type, both deadline dates, the applicant-identification state with the office policy.
   - Right: documents. "Create draft" per question or for several; the editor shows sections with their origin: template text locked, model text with a marked background and "accept" or "edit", placeholders highlighted until filled. Findings of the checks as a list that jumps to the place. Buttons: check, submit, approve or reject (by role), export.
3. **"What the model received"** dialog from the trace endpoint: provider, data class, pseudonymised text.
4. **Audit tab**: events of the case in time order; a button to verify the chain.
5. **Sticky action bar**; unsaved-changes guard; every action reachable by keyboard; focus order follows the reading order; all controls labelled; text scalable to 200 % without loss; contrast at least 4.5:1; status messages announced to assistive technology.
6. Polish UI throughout; all strings in one resource file; dates in the Polish format with the weekday.
7. A "demo mode" switch that loads the scripted demo request and resets the data.

## Acceptance

- [ ] End-to-end test (headless): log in, open the demo request, confirm classes, create a draft, accept model text, fill a placeholder, run checks, submit, approve as reviewer, export. Under 90 seconds of scripted time.
- [ ] Accessibility scan of inbox and case view: no critical or serious finding; keyboard-only run-through of the same path recorded in the status file.
- [ ] With the API returning errors (problem details), the UI shows the message and keeps the user's edits.
- [ ] A draft with a blocker cannot be submitted; the reason is visible.
- [ ] Negative control: with a clerk role, the approve button of the reviewer step is absent and the API refuses the call.
- [ ] `tools/gate.sh fast` passes; screenshots of the three main screens are saved under `docs/assets/screens/` for the pitch.

## Out of scope

Dashboard (WP-A8), redaction UI (WP-A7), counter view (WP-B3).
