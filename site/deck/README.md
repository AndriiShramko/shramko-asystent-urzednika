# Pitch deck: Asystent Urzędnika

Plain HTML, CSS and JavaScript, no build step, no network. Open `index.html` by double-click (works from disk) or at <https://urzad.flyreelstudio.eu/deck/>. Specification: `docs/05-hackathon/presentation/storyboard.md`.

## Presenting
1. Open `index.html` on the projector screen, press `F` for full screen.
2. Press `P`: the presenter window opens (allow pop-ups if asked). Drag it to your laptop screen.
3. Both windows stay in step: navigate in either one.

| Key | Audience window | Presenter window |
|---|---|---|
| `→` `Space` `PageDown` | next slide | next slide |
| `←` `PageUp` | previous slide | previous slide |
| `Home` / `End` | first / last | first / last |
| number then `Enter` | jump to slide | — |
| `1`–`9`, `0` | — | open answer card; `Esc` closes |
| `F` / `P` / `M` | full screen / presenter window / motion on-off | — / — / motion on-off |

The timer starts at 5:00 on the first advance, turns yellow after 4:00 elapsed, red after 5:00. "Reset 5:00" stops and resets it.

## Editing
- **Texts** (screen words, what to say, Russian lines, cues, PDF captions, answer cards, phrases): `slides.js`. Slide 7: set `built: true` when the online form exists, so the presenter reads the "if built" wording.
- **Labels inside drawings**: `scenes.js` (one function per slide; at most three words per label).
- **Numbers on slide 6**: fill `metrics.json` (`null` = not measured, counter hidden), then run `node tools/deck_pdf.mjs`, which also copies the values into `metrics.js` (used when the deck is opened from disk).
- **What works / what is simulated (slide 9)**: `status.json`, then run the same script (it refreshes `status.js`).
- **Demo video (slide 4)**: put `media/demo.mp4` (H.264, muted is fine). It replaces the animated mock automatically.
- Colours: tokens at the top of `deck.css`.

## PDF
`node tools/deck_pdf.mjs` renders `index.html?print=1` (one 1920×1080 page per slide, final frame, caption) to `Asystent-Urzednika.pdf` with Playwright if installed, otherwise with the installed Chrome/Chromium/Edge (`CHROME_PATH` overrides). It prints the size and fails at 10 MB or more.
