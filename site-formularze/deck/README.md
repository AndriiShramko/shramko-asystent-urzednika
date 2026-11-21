# Pitch deck: Od druku do usługi online

Second deck (task "Cyfryzacja formularzy", COI). Plain HTML, CSS and JavaScript, no build step, no network. Open `index.html` by double-click (works from disk) or at <https://formularze.flyreelstudio.eu/deck/>. Specification: `docs/05-hackathon/presentation/storyboard-formularze.md`.

`deck.js` and `deck.css` are unchanged copies of `site/deck/` (same keys, presenter window, print mode); the motion of this deck's drawings is in `scenes.css`.

## Presenting
1. Open `index.html` on the projector screen, press `F` for full screen.
2. Press `P`: the presenter window opens (allow pop-ups if asked). Drag it to your laptop screen.
3. Both windows stay in step: navigate in either one. Do not keep the first deck open in the same browser at the same time (both decks use the same sync channel).
4. If the drawings do not move, the computer has "animation effects" switched off (reduced motion): press `M` once.

| Key | Audience window | Presenter window |
|---|---|---|
| `→` `Space` `PageDown` | next slide | next slide |
| `←` `PageUp` | previous slide | previous slide |
| `Home` / `End` | first / last | first / last |
| number then `Enter` | jump to slide | — |
| `1`–`9`, `0` | — | open answer card; `Esc` closes |
| `F` / `P` / `M` | full screen / presenter window / motion on-off | — / — / motion on-off |

The timer starts at 5:00 on the first advance, turns yellow after 4:00 elapsed, red after 5:00.

## Editing
- **Texts** (screen words, what to say, Russian lines, cues, PDF captions, answer cards, phrases): `slides.js`. Slide 6: set `built: true` when the mObywatel adapter exists, so the presenter reads the "if built" wording.
- **Labels inside drawings**: `scenes.js` (one object per slide; at most three words per label).
- **Demo videos**: put `media/demo-1.mp4` (slide 3, digitising a form) and `media/demo-2.mp4` (slide 4, visitor and clerk) next to `index.html` (H.264, muted is fine). Each replaces its animated mock automatically; a missing file leaves the mock.
- **Numbers**: fill `metrics.json` (`null` = not measured = hidden). Slide 3 shows `digitise_seconds`, `fields_detected_pct`, `forms_digitised`; slide 4 shows `fill_seconds`. Labels are in `slides.js` (`metricLabels`).
- **What works / what is simulated (slide 7)**: `status.json`.
- After changing `metrics.json` or `status.json`, run the PDF command below: it also refreshes `metrics.js` and `status.js` (used when the deck is opened from disk).

## PDF and checks
- `node tools/deck_pdf.mjs site-formularze/deck Od-druku-do-uslugi.pdf` renders `index.html?print=1` (one 1920×1080 page per slide, final frame, caption) with the installed Chrome/Edge (`CHROME_PATH` overrides). It fails at 10 MB or more.
- `python -X utf8 tools/deck_smoke.py --deck site-formularze/deck --out docs/assets/deck-formularze --presenter-slide 4` loads every slide headless, reports console errors, writes screenshots and a contact sheet, and decodes the QR code on the last slide.
