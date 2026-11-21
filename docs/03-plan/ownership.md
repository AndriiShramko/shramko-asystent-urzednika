# Ownership: one path, one work package

An agent edits only the paths of its own package. Everything not listed is lead-only. Modules register themselves (routes file inside the module, feature folder with its own route file), so no package needs to edit a central list.

| Path | Owner |
|---|---|
| `apps/api/app/main.py`, `apps/api/app/core/**`, `apps/api/pyproject.toml`, `tools/gate.sh`, `tools/precommit_scan.py`, `tools/testdata/**`, root manifests, `contracts/**`, `packages/api-client/**` | WP-00, afterwards the lead |
| `apps/api/app/modules/cases/**`, `apps/api/app/modules/audit/**`, `apps/api/tests/cases/**` | WP-A1 |
| `apps/api/app/modules/llm/**`, `apps/api/app/modules/pii/**`, `apps/api/tests/llm/**`, `apps/api/tests/pii/**` | WP-A2 |
| `apps/api/app/modules/knowledge/**`, `data/kb/**`, `apps/api/tests/knowledge/**` | WP-A3 |
| `apps/api/app/modules/analysis/**`, `prompts/udip-analysis*.md`, `data/eval/**`, `apps/api/tests/analysis/**` | WP-A4 |
| `apps/api/app/modules/drafts/**`, `data/templates/udip/**`, `prompts/udip-draft*.md`, `apps/api/tests/drafts/**` | WP-A5 |
| `apps/clerk-web/**` except `src/features/counter/**`, `src/features/redaction/**`, `src/features/dashboard/**` | WP-A6 |
| `apps/api/app/modules/redaction/**`, `apps/clerk-web/src/features/redaction/**` | WP-A7 |
| `apps/api/app/modules/similar/**`, `apps/api/app/modules/dashboard/**`, `apps/clerk-web/src/features/dashboard/**` | WP-A8 |
| `apps/api/tests/security/**`, `docs/02-architecture/threat-model-check.md` | WP-A9 |
| `apps/api/app/modules/public_demo/**`, `apps/clerk-web/src/features/public/**` | WP-A10 |
| `apps/api/app/modules/forms/**`, `data/forms/**` (descriptors, bundles), `data/canonical-profile.schema.json` | WP-B1 |
| `apps/api/app/modules/sessions/**`, `apps/relay/**`, `apps/visitor-pwa/**` | WP-B2 |
| `apps/clerk-web/src/features/counter/**` | WP-B3 |
| `apps/api/app/modules/identity/**`, `apps/visitor-pwa/src/features/scan/**`, `apps/bridge/**` | WP-B4 |
| `apps/api/app/modules/checker/**`, `prompts/form-check*.md` | WP-B5 |
| `apps/api/app/modules/onboarding/**`, `prompts/form-onboarding*.md` | WP-B6 |
| `README*`, `AGENTS.md`, `START_HERE.md`, `docs/**` except each package's own status file, `research/**` | lead |
| `docs/03-plan/wip/WP-<id>.status.md` | the builder of that package |

Shared files that tempt several packages:

- **Dependencies.** A builder adds a Python dependency by writing the line into its status file under "Requests to lead"; the lead adds it to `apps/api/pyproject.toml` on `main` and the builder merges `main`. The same for `package.json` of a front end owned by another package. Reason: lock-file conflicts are the most common cause of broken merges.
- **Database migrations.** One migration file per package, named with the package id; no editing of another package's migration.
- **Prompts** live in `prompts/` as files, one per task, owned by the package that uses them; code loads them by name.
- **Test data.** Generators in `tools/testdata` belong to WP-00; a package adds its own fixtures under its own tests folder.
