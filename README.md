# Ubuntu IPA and Theos Toolkit

GitHub Actions workflows for experimental iOS IPA processing and **ARM64 Logos tweak cross-compilation on Ubuntu**, without a macOS runner or Xcode.

## 1. Compile your own test tweak (Ubuntu / Theos)

Workflow: [Ubuntu Theos ARM64](.github/workflows/theos-arm64.yml)

- Runner: `ubuntu-22.04`
- Theos setup: `Randomblock1/theos-action@v1` (installs toolchain and iOS SDK)
- Sources: `tweak/Tweak.xm` (Objective-C/Logos), `tweak/Makefile`, `tweak/UbuntuDemo.plist`, `tweak/control`
- Build command: `make clean package FINALPACKAGE=1`
- Output: downloadable GitHub Actions artifact with `UbuntuDemo-arm64.dylib` and a `.deb` package
- Checks: `scripts/check_macho_arm64.py` verifies ARM64 / Mach-O dylib header

### Start it

1. Open **Actions** in this repository.
2. Select **Ubuntu Theos ARM64**, choose **Run workflow** on `main`.
3. When the run succeeds, download **UbuntuDemo-arm64-Theos** in **Artifacts**.
4. Edit `tweak/Tweak.xm` to experiment with your own Logos code and push your change.

This is a **test tweak** filtered to the iOS Settings app. It logs view appearances and does not remove ads or unlock features. It is built for tweak-injection environments: **the `.deb` is not an installable IPA**. Packaging a tweak inside a sideloaded IPA and properly re-signing it is a separate process.

**Important:** Theos on Ubuntu can build supported Objective-C/Logos ARM64 components. It does **not** replace all Xcode features, and it does not automatically produce normal standalone App Store apps.

## 2. Validate or repackage an existing IPA

Workflow: [Ubuntu IPA Toolkit](.github/workflows/ubuntu-ipa.yml)

Current features:
- Validate ZIP structure, `Payload/*.app/Info.plist`, app executable and bundle identifier.
- Repackage an existing IPA unchanged.
- Upload a validation report or repackaged **unsigned** IPA.

The IPA workflow expects a file in `input/` and fails until one is provided. Do **not** commit third-party copyrighted IPA files or signing credentials to this public repository. A secure private upload mechanism can be added later.

Local use: `python3 scripts/ipa_tool.py validate your.ipa --output output`.

## Limits

No FairPlay decryption, DRM bypass, signing certificates, SwiftUI/Xcode project support or tweak injection is included. An altered signed iOS app bundle generally needs signing again to install, and not every tweak runs inside jailed apps.
