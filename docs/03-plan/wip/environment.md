# Build machine: environment check (WP-F1 step 0)

Measured on 21 November 2026 with `python tools/env_check.py --md` (reads only, changes nothing). Path (b) of design 9.1 is in force: no Docker on the laptop, CI builds and proves the image.

| Piece | State | Detail | If missing |
|---|---|---|---|
| Python 3.14 | MISSING | absent (running 3.13.3) | install per user (no administrator rights); until then develop on 3.13, the source stays compatible |
| Docker | MISSING | not found | owner only: WSL 2 and Docker Desktop; else CI builds the image (WP-F20) |
| WSL | MISSING | not installed | owner only: `wsl.exe --install` |
| Tesseract + pol | MISSING | not found | the second OCR engine stands in for development; Tesseract tests run in CI |
| Node 22 | ok | v22.16.0 | |

Two items cannot be measured from the laptop and are taken from the facts of 21 November given in the brief of this stage:

- Push of a workflow file: proven (workflows run).
- Actions and the registry: proven; the image goes to `ghcr.io/andriishramko/shramko-asystent-urzednika` and the package is public.

Base-image digests in `apps/converter/Dockerfile` were read from the Docker Hub registry API the same day (index digests, multi-architecture).
