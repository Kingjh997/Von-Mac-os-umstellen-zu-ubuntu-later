# Ubuntu IPA Toolkit

An experimental GitHub Actions workflow to inspect and repackage existing iOS IPA archives on Ubuntu, without macOS or Xcode.

## What works
- Validate the IPA ZIP structure and app Info.plist
- Check app executable presence and bundle identifier
- Repackage an IPA without modifying its contents
- Upload an unsigned IPA artifact

## What this does NOT do
- Compile arbitrary SwiftUI / Xcode projects on Linux
- Remove FairPlay encryption, bypass DRM, or sign with Apple tools
- Inject tweaks or change the app's code
- Guarantee that a repackaged IPA is installable: any changed signed bundle needs valid re-signing

## Usage
Put an IPA you are authorized to process in `input/` (do not commit third-party copyrighted IPA files to a public repository). Trigger the `Ubuntu IPA Toolkit` workflow with `validate` or `repackage`.

For private IPA inputs, a secure artifact-input mechanism should be added before use. The current workflow deliberately fails when `input/` is empty.

Run locally: `python3 scripts/ipa_tool.py validate your.ipa --output output`.
