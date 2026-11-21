# WP-F9 Front end, view "Przegląd": status

Branch: wp/F9-review-web   Stage now: core (done) -> integration / acceptance next

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
- [ ] Served by `app/main.py`: the mount `/ui` already exists and looks for `apps/review-web/dist` (checked by a real run, see Evidence when done)
- [ ] Every-device check: Playwright, Chromium + Firefox or WebKit, 375 / 768 / 1280 px, screenshot per width and engine (script `scripts/devices.mjs`)
- [ ] Real upload through the running service (synthetic PDF from `tools/ci/make_fixtures.py`)
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

## Negative control
With the sidecar missing (or invalid) the form is still listed and downloadable and the page says what is absent: `tests/lib.test.ts` "negative control: with the sidecar missing or broken" and `tests/ui.test.ts` "negative control: sidecar missing, the form is still shown". A wrong hash is flagged ("bad"), and a colour pair below 4.5:1 is measured as failing (`contrast.test.ts`).

## Requests to lead
- None for the core. The Dockerfile `ui` stage works with the folder as it is (`npm ci`, `npm run build`, `dist/`). Playwright is not a dependency of the package (installed with `--no-save` when the device check runs).

## Cost notes
- core: the most turns went to reading the sidecar shape (the REST sidecar nests `meta.origins`, the contract keeps them at the top level; both are read). Cheaper next time if the lead fixes one shape in the brief.
