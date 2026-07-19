# ISTQB Prep Web App

This repository now includes a ready-to-run web app version of ISTQB prep tests.

## Quick start

1. Start a static server in the repository root:
   - `python3 -m http.server 4173`
2. Open in browser:
   - `http://127.0.0.1:4173`

## iPhone install (without App Store)

1. Open the app URL in Safari on iPhone.
2. Share -> Add to Home Screen.
3. Launch from the new icon.

## MVP features

- Start screen and exam selection (A/B/C/D)
- Questions with options
- Single-select and multi-select behavior
- Correct/wrong highlighting after selection
- Explanation block (collapsed by default)
- Previous / Next / Finish controls
- Progress bar and answered counter
- Results: correct / incorrect / unanswered / total
- Back to home and start a new test

## Data files

- `data/exam_A.json`
- `data/exam_B.json`
- `data/exam_C.json`
- `data/exam_D.json`

## PWA

The app includes:

- `manifest.webmanifest`
- `sw.js` (offline cache for app shell + exam data)

## Notes

- Existing iOS SwiftUI folder `ISTQBPrepApp` is kept in repo, but for old Mac hardware use the web app flow above.
- More detailed deployment/setup instructions: `WEB_SETUP.md`.

## Copyright and usage

- ISTQB content in this repository is attributed to the International Software Testing Qualifications Board (ISTQB).
- Review the local notice before publishing or redistributing: `COPYRIGHT_NOTICE.md`.
- Use in permitted scenarios (especially personal and non-commercial learning) and seek ISTQB permission for unclear or broader usage.
