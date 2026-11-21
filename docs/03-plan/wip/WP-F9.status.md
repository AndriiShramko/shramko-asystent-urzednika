# WP-F9 Front end, view "Przegląd": status

Branch: wp/F9-review-web   Stage now: acceptance (done)

Scope of the first build (lead, 21 Nov 17:25; D22, D25): review view first, three languages, every-device check. Later, not now: paper page with outlined places and two ink colours, decision cards, batch table.

## Status
- [x] Scaffold `apps/review-web` (Vite 7, TypeScript, vanilla, no runtime dependency), `package-lock.json`, `base './'` so the build works under `/ui/`
- [x] Dictionaries pl/en/es keyed by stable codes (UI, 32 warning codes, 20 problem codes); type-checked equal keys
- [x] Upload by drag or button with the bearer token (memory only), call `POST ../v1/forms/convert?report=1`, multipart reader on bytes
- [x] Result view: summary, fields of the matter first (page + snippet), warnings grouped by code in plain words, standard sections collapsed, unknown-origin fields, form JSON read / copy / download byte-equal, SHA-256 against `X-Form-SHA256`
- [x] Refusal shown as its plain reason (translated by code, Polish `detail` kept apart); missing sidecar says what is absent (negative control)
- [x] Language switch pl (default) / en / es, remembered in `localStorage`
- [x] Unit tests (vitest + happy-dom): 43 pass; own contrast-token check (WCAG AA pairs)
- [x] Licence list `LICENCES-FRONTEND.md` (script `npm run licences`): 61 packages, all allowed, 0 runtime dependencies
- [x] Served by `app/main.py`: the mount `/ui` already existed and finds `apps/review-web/dist`; no change under `apps/converter/app` was needed (real run: `GET /ui/` 200, assets relative)
- [x] Every-device check: Playwright 1.x with Chromium and Firefox, 375 / 768 / 1280 px, `scripts/devices.mjs`; screenshots in `apps/review-web/evidence/`
- [x] Real upload through the running native service (`AUTH_MODE=off`, synthetic PDF of `tools/ci/make_fixtures.py`): form shown, SHA-256 matches `X-Form-SHA256`
- [x] WebKit ran in the integration check (21 pass); the 54-state device check ran on Chromium and Firefox only
- [x] Token path against a real service with `AUTH_MODE=jwt` (HS256, synthetic key): no token, wrong key, expired -> plain refusal, no form; token with `scope: convert` -> form
- [x] Judged sets 8 and 9 and both reference sets (1, 5) loaded through the page, 3 engines: form shown, SHA-256 agrees, matter section present (12 of 12)
- [ ] Later (not in the first build): paper page with outlined places, two inks, decision cards, batch table

## Decisions
- Vanilla TypeScript, no framework / smallest bundle (42 kB, 15 kB gzip), zero runtime licences to track / rules out components libraries.
- Upload with `?report=1` and read the multipart by bytes / the form part stays byte-equal to REST (D1) and the sum can be checked against `X-Form-SHA256` / rules out `JSON.parse` + re-serialise for copy and download.
- Vite 7, not 8 / Vite 8 pulls `lightningcss` (MPL-2.0), MPL needs the lead's yes (rule 4) / rules out Vite 8 until the lead decides.
- Origin of a field = `meta.origins[id]` (or top-level `origins`), else the nearest ancestor's; no sidecar means "unknown", never a guess. Snippet from `meta.evidence[id]` (object or list), "not found" when absent / no invented place.
- `X-Converter-Warnings` is read tolerantly (first number = count, UPPER_CASE words = codes) because WP-F14b has not fixed its spelling / change one function when it does.
- Colours are CSS tokens checked as pairs by a test; no axe-core (MPL-2.0) / our own rules only.

## Evidence
| Acceptance item | Command | Result | Commit it ran on |
|---|---|---|---|
| Core tests | `cd apps/review-web && npm test` | 43 passed (3 files) | see git log |
| Type check and build | `npm run build` | tsc clean, dist 42 kB js + 4.6 kB css | see git log |
| Licences | `npm run licences` | 61 packages, 0 not allowed, 0 runtime | see git log |
| Every device | `node scripts/devices.mjs --engines chromium,firefox ...` (service on a free port, `AUTH_MODE=off`) | 54 page states (2 engines x 3 widths x 3 languages x idle/result/refusal): 0 findings (no horizontal scroll, nothing outside the viewport, no clipped text, controls >= 24 px, no overlap, all reachable with Tab, no request outside the origin). First run found one: checkbox 20 px, fixed to 24 px | this commit |
| Screenshots (result state, Polish) | `apps/review-web/evidence/` | `chromium-375.png`, `chromium-768.png`, `chromium-1280.png`, `firefox-375.png`, `firefox-768.png`, `firefox-1280.png`; full report `devices-report.json` | this commit |
| Fast gate | `bash tools/gate.sh fast` | 652 passed, 2 skipped; links 21 passed | e01be5e + this commit's front-end only changes |

- Integration check: `apps/review-web/scripts/integration.mjs` (files read in place via the paths of `tools/coi_paths.py`, nothing copied). Result: 21 PASS lines, `all passing` (3 engines x [3 refusals + 4 forms]). Fast gate: 670 passed, 2 skipped, links 21 passed.

## Acceptance run (beebab6, main already merged: "Already up to date")
- `npm test`: 43 passed. `npm run build`: tsc clean, 42.2 kB js. `npm run licences`: 61 packages, 0 outside the list, 0 runtime.
- `bash tools/gate.sh fast`: 670 passed, 2 skipped; links 21 passed; "gate: fast PASSED on beebab6".
- Negative control run now: the heading of the missing-sidecar notice in `src/ui/result.ts` blanked -> `ui.test.ts` "negative control: sidecar missing..." FAILED (1 failed, 42 passed); file restored -> 43 passed.
- Not in the first build (per scope): paper page, decision cards, batch table.

## Negative control
With the sidecar missing (or invalid) the form is still listed and downloadable and the page says what is absent: `tests/lib.test.ts` "negative control: with the sidecar missing or broken" and `tests/ui.test.ts` "negative control: sidecar missing, the form is still shown". A wrong hash is flagged ("bad"), and a colour pair below 4.5:1 is measured as failing (`contrast.test.ts`).

## Requests to lead
- None for the core. The Dockerfile `ui` stage works with the folder as it is (`npm ci`, `npm run build`, `dist/`). Playwright is not a dependency of the package (installed with `--no-save` when the device check runs).

## Notes for the next stage
- The sidecar of the current pipeline has `meta.origins` but no `meta.evidence`, so fields of the matter show "no place on the paper found" (honest gap, tested). The snippet appears as soon as the service writes `meta.evidence`.
- Re-run the device check: build (`npm run build`), start `AUTH_MODE=off bash tools/gate.sh py -m converter serve --port <free>`, `npm install --no-save playwright`, `PLAYWRIGHT_BROWSERS_PATH=.playwright npx playwright install chromium firefox`, then `node scripts/devices.mjs --engines chromium,firefox --base http://127.0.0.1:<port>/ui/ --file <synthetic pdf> --bad <text file named .png> --out evidence`. Port 8099 was taken by another process on this machine.

- Integration found: a token without `scope: convert` gets 403 SCOPE; the page showed it as a plain refusal (first run, before the script minted the scope).

## Cost notes
- core: the most turns went to reading the sidecar shape (the REST sidecar nests `meta.origins`, the contract keeps them at the top level; both are read). Cheaper next time if the lead fixes one shape in the brief.
- integration: the most turns went to path forms (Git Bash `/c/...` vs Windows `C:/...` for Playwright) and the missing `scope` claim. Cheaper: pass Windows paths and say in the brief that the token needs `scope: convert`.
- acceptance: few turns; one batch of checks, one break/restore. Cheaper: none needed.
