# Publishing: the project site, the deck and test versions

Public address: **<https://urzad.flyreelstudio.eu>** on the owner's server. Set up on 21 November 2026.

## How it works

The server keeps a mirror of this repository and serves the folder [`site/`](../../site/) as static files. A scheduled job on the server pulls `main` every two minutes. **To publish, commit into `site/` and push `main`. Nothing else is needed, from any computer.** No keys or logins for the server are required on the build machine.

| Address | Folder in the repository | What |
|---|---|---|
| `/` | `site/index.html` | landing page (Polish) |
| `/deck/` | `site/deck/` | the pitch deck (audience window, presenter window, print mode) |
| `/deck/media/demo.mp4` | `site/deck/media/` | the demo video, played by slide 4 |
| `/app/` | `site/app/` | a static build of the clerk web app in demo mode (see below) |
| `/health` | (server) | returns `ok` |

Check after a push: wait up to two minutes, open the address in a private window, hard-reload. HTML is served with `Cache-Control: no-cache`; media is cached for ten minutes.

## Test versions without a server process

The server runs **no application code** for this project: it has little free disk and memory and hosts the owner's other services. Test versions are therefore published as static builds:

1. The clerk web app has a **demo mode** in which every API call is answered in the browser from recorded responses (the same recordings that the mock model provider uses). No backend is needed.
2. `npm run build:demo` in `apps/clerk-web` writes the build with base path `/app/`; `tools/publish_site.sh` copies it to `site/app/`, commits and pushes.
3. A juror opens `https://urzad.flyreelstudio.eu/app/` and clicks through the scripted request without installing anything.

The real backend with a real model runs on the build laptop for the live demo. If the jury must reach a live backend from their own devices, the fallbacks in order are: a tunnel from the laptop (for example a quick tunnel of a tunnelling tool) with the address shown on a slide; the static demo; the recorded video. Running the backend on the owner's server needs the owner's explicit decision and a person with server access; it is not part of the plan.

## Limits

- Only `site/` is checked out on the server (sparse, shallow). Keep it small: no file over 25 MB, the whole folder under 100 MB.
- Never put secrets, real personal data or the vendor SDK into `site/`. Everything there is public the moment it is pushed.
- Build output is committed only into `site/app/`; do not commit build output anywhere else.
- The site is static: no forms that post to this server, no cookies, no analytics.

## Server side (for the record; nothing to do here during the event)

Container `urzad-web` (nginx, memory limit 64 MB) behind the server's shared reverse proxy with an automatic certificate; mirror in `/home/fpv/urzad/repo`; `pull.sh` from cron every two minutes with a disk guard (it skips fetching when less than 2 GB is free) and a log; the folder is in the server's backup registry.
