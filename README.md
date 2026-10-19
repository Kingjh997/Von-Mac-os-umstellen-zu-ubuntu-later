# Ubuntu IPA + Theos ZIP-zu-DYLIB Builder

Build and package supported iOS ARM64 Theos/Logos tweaks **using Ubuntu GitHub Actions (no macOS runner, no Xcode)**. The GitHub Actions artifacts are automatically downloadable as ZIP files.

## Option 1: Download a ready-made ZIP containing .dylib and .deb

Workflow: **[Ubuntu Theos ARM64](.github/workflows/theos-arm64.yml)**.

1. Open [Actions](../../actions) and select **Ubuntu Theos ARM64**.
2. Run the workflow on `main` (or select a successful run).
3. Scroll to **Artifacts** and download **UbuntuDemo-arm64-Theos.zip**.
4. Extract it to get **UbuntuDemo-arm64.dylib**, its **.deb package**, and **UbuntuDemo-source-example.zip** (the example project source code).

This runs on Ubuntu 22.04 and compiles the version-controlled sample in `tweak/`. The reusable source ZIP can be uploaded back using option 2.

## Option 2: Upload a Theos source ZIP; build a .dylib for the IPA Frameworks directory

Workflow: **[Ubuntu ZIP to Frameworks DYLIB](.github/workflows/build-from-zip.yml)**.

1. Prepare a ZIP containing the **source files for one Theos tweak** (not just an IPA or an already compiled binary). It needs **Makefile** and **control** in the same directory, alongside source files such as `Tweak.xm` and `YourTweak.plist`. A single enclosing folder is fine.
2. Open the **[source-zips folder](source-zips)** on GitHub.
3. Choose **Add file → Upload files**, upload `MyTweak.zip` to this folder, then **Commit changes** to `main`. **Do not upload private keys, certificates, credentials or third-party source code without permission.** This repository is public.
4. GitHub automatically starts **Ubuntu ZIP to Frameworks DYLIB**. Alternatively, open **Actions → Ubuntu ZIP to Frameworks DYLIB → Run workflow**. Set **output_mode = framework_dylib** (the default). Leave `zip_path` blank to compile all ZIPs in `source-zips/`, or use `source-zips/MyTweak.zip` to build just one file.
5. After a successful run, download the **Ubuntu-Frameworks-or-Theos-results.zip** artifact. Inside, each source ZIP gets its own folder with **Frameworks/YourTweak.dylib**, **YourTweak-arm64.dylib**, and **INSTALLATION.txt**. Select **output_mode = tweak_package** instead if you specifically want the older jailbreak-style **.dylib + .deb** package output.

**Example matching your upload:** A Theos ZIP containing `Tweak.m`, `EMWallet.c`, `Makefile`, `control`, and a plist can be compiled with this workflow. The archive `EnergyManager-Diagnose-Test-v1(2).zip` supplied in chat matches this source layout; it has NOT been committed to this public repository. Upload it yourself to `source-zips/` to compile it. The intended output name is `EMReadOnlyDiagnostics.dylib`, subject to a successful build. Its features remain read-only diagnostics and simulated test values, not game-state modifications.\n\n**Test ZIP:** `source-zips/UbuntuDemo-test-source.zip` contains a small test tweak to validate the end-to-end workflow. Use it to check the setup before providing your own code.

### Important technical limits

- These ZIPs contain **Theos source code**, not arbitrary files: renaming an IPA or binary to `.zip` cannot produce tweak source code.
- The pipeline builds supported **ARM64 Mach-O dylibs** using a Linux cross-compiler and an iOS SDK. The default Frameworks mode converts simple Theos tweak projects to standalone libraries with an **@rpath install name**, and checks for unwanted CydiaSubstrate/libhooker/ElleKit dependencies. The optional `tweak_package` mode also builds Debian tweak packages.
- Building a tweak does not automatically install or inject it into an IPA, make it compatible with jailed iPhones, or sign an IPA for ESign. iOS app injection and valid signing require separate steps.
- Not all Xcode or SwiftUI projects can be built under Linux.
- Source ZIPs contain executable build instructions. **Only upload trusted source code.** ZIP extraction blocks path traversal, links, unsafe entry types, encryption and oversized archives, but cannot make malicious Makefiles safe to run.

## Option 3: Validate or repackage existing IPA archives (without compiling code)

Workflow: **[Ubuntu IPA Toolkit](.github/workflows/ubuntu-ipa.yml)**.

- Checks IPA ZIP layout, `Payload/*.app/Info.plist`, bundle ID, executable.
- Optionally repackages the IPA as an **unsigned** archive.
- Currently needs an IPA under `input/`, which is excluded from Git. A secure upload interface has not yet been implemented.

Do not commit copyrighted third-party IPA files or private signing material to this public repo. No FairPlay decryption, DRM bypass, Xcode project compilation, tweak injection or Apple app-signing service is implemented.


## Original-Xcode-SDK vs. Ubuntu: überprüfbarer Buildvergleich

Der Workflow **[Compare Ubuntu vs Xcode SDKs](.github/workflows/compare-sdks.yml)** verwendet auf beiden Systemen dieselbe *öffentliche, neutrale* Logos-Testquelle (`tweak/Tweak.xm`). Er baut kein Energy-Manager-Menü nach, verändert keine Spielwerte und veröffentlicht weder die Energy-Manager-IPA noch deren Quellcode.

Er ermittelt und protokolliert:
- Auf macOS: `xcodebuild -version`, Apple-Clang, offizielles iPhoneOS-SDK über `xcrun --sdk iphoneos --show-sdk-path`.
- Auf Ubuntu: Clang-Versionen, verfügbare Theos-SDKs, Framework-Verzeichnisse, Header und vorhandene Theos-Toolchain-Compiler.
- Beide Mach-O-Binärdateien: ARM64, Install-Name, Mindest-iOS, tatsächliche SDK-Build-Version, dynamisch verknüpfte Bibliotheken, Suchpfade, Code-Signature-Eintrag und SHA-256.
- Identität des Quellcodes und der Theos-Revision auf beiden Runnern.

**Bereits bestätigt:** Xcode 16.4 / iPhoneOS 18.5 auf macOS 15; Theos iPhoneOS 16.5 auf Ubuntu 22.04. Beide Systeme konnten aus demselben Quellcode ARM64-Dylibs mit gleichem Install-Name, gleichem iOS-Minimum 14.0 und denselben Bibliotheksabhängigkeiten bauen. Die Binärdateien unterscheiden sich in SDK-Version, Größe und Code-Signature-Eintrag. Das beweist keine identische iPhone-Laufzeit.

**SDK- und Framework-Abweichungen** stehen im GitHub Actions-Artefakt `sdk-xcode-vs-ubuntu-comparison` (Datei `comparison.md`). Beide Runner verwenden ihre jeweils rechtmäßig bereitgestellten SDKs; das originale Apple-SDK wird nicht nach Ubuntu kopiert.

### Laufzeit / IPA statisch prüfen

Das Skript `scripts/ipa_loader_audit.py` untersucht **lokal, ohne Änderung der IPA**, welche ARM64-Frameworks eingebettet sind und ob das ausführbare Hauptprogramm eine erwartete Dylib referenziert:

```bash
python3 scripts/ipa_loader_audit.py "MeineApp.ipa" --library EMReadOnlyDiagnostics.dylib --output ipa-loader-report.json
```

Eine eingelagerte Dylib wird dadurch **nicht automatisch ausgeführt**. Für ein sicher nachgewiesenes Laden sind ein kompatibler Ladevorgang, korrekte Signierung und ein Geräte-Laufzeittest notwendig. Das Skript prüft Signierungsmetadaten nicht kryptografisch.

### Frameworks- statt Jailbreak-Paket

`scripts/convert_to_framework_library.py` entfernt in `framework_dylib`-Builds die rootless/roothide-Paketeinstellung, damit keine nur für Jailbreaks gedachten `/var/jb`-/`.jbroot`-Suchpfade entstehen. Der Mach-O-Validator lehnt solche Pfade im Frameworks-Modus nun ab. Diese Änderung betrifft die extrahierte Arbeitskopie des Quellcodes, nicht die eingereichte ZIP.

**Wichtig:** Der originale Quellcode des auf den Screenshots sichtbaren `Lab`-Menüs liegt in den hier geprüften Projekten nicht vor. Ein Wechsel des iOS-SDK erzeugt dieses Menü nicht automatisch. Der Vergleich bestätigt nur die technische Cross-Compile-Fähigkeit.
