# Web app setup (no Xcode)

## Run locally on Mac

1. Clone repository.
2. Open terminal in repository root.
3. Run a static server, for example:
   - python3 -m http.server 4173
4. Open Safari:
   - http://127.0.0.1:4173

## Install on iPhone as app icon

1. Open the app URL in Safari on iPhone.
2. Tap Share.
3. Tap Add to Home Screen.
4. Launch from the new icon.

## Deploy for easy phone access

Option A: GitHub Pages
1. In GitHub repository settings, enable Pages from branch `main` and folder `/ (root)`.
2. Wait for publish.
3. Open published URL on iPhone in Safari and Add to Home Screen.

Option B: Netlify/Vercel
1. Import repository.
2. Deploy as static site.
3. Open deployment URL on iPhone in Safari and Add to Home Screen.

## Features included in this web version

- Start screen and exam selection (A, B, C, D)
- Question flow with Previous / Next / Finish
- Single-select and multi-select support
- Correct and wrong highlighting after selection
- Collapsed explanation block per question
- Progress bar and answered counter
- Result screen with correct / incorrect / unanswered totals
- Restart to home

## Data source

Exams are loaded from:
- data/exam_A.json
- data/exam_B.json
- data/exam_C.json
- data/exam_D.json
