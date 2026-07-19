# Xcode setup and iPhone install

## 1. Generate Xcode project on Mac

1. Install Xcode from App Store.
2. Install XcodeGen:
   - brew install xcodegen
3. Open Terminal in this folder and run:
   - xcodegen generate

This will create ISTQBPrepApp.xcodeproj.

## 2. Open and set signing

1. Open ISTQBPrepApp.xcodeproj in Xcode.
2. Select project -> target ISTQBPrepApp -> Signing & Capabilities.
3. Enable Automatically manage signing.
4. Select your Team (Apple ID is enough for local testing).
5. Keep bundle identifier unique, for example:
   - com.<yourname>.istqbprep

## 3. Verify bundled exam files

In target Build Phases -> Copy Bundle Resources, ensure these files are present:
- Resources/exam_A.json
- Resources/exam_B.json
- Resources/exam_C.json
- Resources/exam_D.json

## 4. Run on iPhone

1. Connect iPhone.
2. Select your device in Xcode run destination.
3. Build and Run.
4. If prompted on device:
   - enable Developer Mode
   - trust developer profile

## 5. Notes

- App is portrait-only by design.
- No backend or integrations are required.
- For free Apple ID, signing may expire in about 7 days.
