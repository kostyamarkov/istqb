# ISTQBPrepApp (minimal)

This folder contains a minimal SwiftUI app implementation for iPhone portrait mode.

## Included functionality

- Start screen with `Start test`
- Exam selection screen: A, B, C, D
- Question screen with options
- Progress bar and answered counter
- Single-select and multi-select support (based on `correctOptions` count)
- Immediate answer evaluation when selecting options
- Correct and selected-answer highlighting
- Collapsed explanation block shown after first interaction
- Bottom controls: Previous, Next, Finish
- Result screen with totals: Correct, Incorrect, Unanswered

## Files to add to your Xcode project

Add all Swift files from these folders to your app target:

- `Models`
- `Services`
- `ViewModels`
- `Views`
- `ISTQBPrepApp.swift`

Add JSON files from `Resources` to the app target as bundled resources:

- `exam_A.json`
- `exam_B.json`
- `exam_C.json`
- `exam_D.json`

## Notes

- The app locks orientation to portrait.
- UI is intentionally simple: white background, text-first layout, lightweight controls.

## Generate Xcode project

This repository contains source files and an XcodeGen spec.

1. Install XcodeGen on Mac: `brew install xcodegen`
2. In this folder run: `xcodegen generate`
3. Open generated `ISTQBPrepApp.xcodeproj` in Xcode

Detailed steps: see `XCODE_SETUP.md`.
