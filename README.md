# Ubuntu IPA + Theos ZIP-zu-DYLIB Builder

Build and package supported iOS ARM64 Theos/Logos tweaks **using Ubuntu GitHub Actions (no macOS runner, no Xcode)**. The GitHub Actions artifacts are automatically downloadable as ZIP files.

## Option 1: Download a ready-made ZIP containing .dylib and .deb

Workflow: **[Ubuntu Theos ARM64](.github/workflows/theos-arm64.yml)**.

1. Open [Actions](../../actions) and select **Ubuntu Theos ARM64**.
2. Run the workflow on `main` (or select a successful run).
3. Scroll to **Artifacts** and download **UbuntuDemo-arm64-Theos.zip**.
4. Extract it to get **UbuntuDemo-arm64.dylib**, its **.deb package**, and **UbuntuDemo-source-example.zip** (the example project source code).

This runs on Ubuntu 22.04 and compiles the version-controlled sample in `tweak/`. The reusable source ZIP can be uploaded back using option 2.

## Option 2: Upload a Theos source ZIP; get .dylib and .deb back

Workflow: **[Ubuntu Build from ZIP](.github/workflows/build-from-zip.yml)**.

1. Prepare a ZIP containing the **source files for one Theos tweak** (not just an IPA or an already compiled binary). It needs **Makefile** and **control** in the same directory, alongside source files such as `Tweak.xm` and `YourTweak.plist`. A single enclosing folder is fine.
2. Open the **[source-zips folder](source-zips)** on GitHub.
3. Choose **Add file → Upload files**, upload `MyTweak.zip` to this folder, then **Commit changes** to `main`. **Do not upload private keys, certificates, credentials or third-party source code without permission.** This repository is public.
4. GitHub automatically starts **Ubuntu Build from ZIP**. Alternatively, open **Actions → Ubuntu Build from ZIP → Run workflow**. Leave `zip_path` blank to compile all ZIPs in `source-zips/`, or use `source-zips/MyTweak.zip` to build just one file.
5. After a successful run, download the **Ubuntu-built-dylib-and-deb.zip** artifact. Inside, find a folder named for each source ZIP containing its built ARM64 **.dylib** and **.deb**.

**Test ZIP:** `source-zips/UbuntuDemo-test-source.zip` contains a small test tweak to validate the end-to-end workflow. Use it to check the setup before providing your own code.

### Important technical limits

- These ZIPs contain **Theos source code**, not arbitrary files: renaming an IPA or binary to `.zip` cannot produce tweak source code.
- The pipeline builds supported **ARM64 Mach-O dylibs** and **Theos Debian tweak packages** using a Linux cross-compiler and an iOS SDK.
- Building a tweak does not automatically install or inject it into an IPA, make it compatible with jailed iPhones, or sign an IPA for ESign. iOS app injection and valid signing require separate steps.
- Not all Xcode or SwiftUI projects can be built under Linux.
- Source ZIPs contain executable build instructions. **Only upload trusted source code.** ZIP extraction blocks path traversal, links, unsafe entry types, encryption and oversized archives, but cannot make malicious Makefiles safe to run.

## Option 3: Validate or repackage existing IPA archives (without compiling code)

Workflow: **[Ubuntu IPA Toolkit](.github/workflows/ubuntu-ipa.yml)**.

- Checks IPA ZIP layout, `Payload/*.app/Info.plist`, bundle ID, executable.
- Optionally repackages the IPA as an **unsigned** archive.
- Currently needs an IPA under `input/`, which is excluded from Git. A secure upload interface has not yet been implemented.

Do not commit copyrighted third-party IPA files or private signing material to this public repo. No FairPlay decryption, DRM bypass, Xcode project compilation, tweak injection or Apple app-signing service is implemented.
