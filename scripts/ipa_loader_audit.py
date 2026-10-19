#!/usr/bin/env python3
"""Read-only static IPA dyld audit; never modifies, signs or injects an IPA."""
import argparse
import json
from pathlib import Path
import plistlib
import zipfile
from macho_audit import inspect

def audit(ipa, expected):
    with zipfile.ZipFile(ipa) as z:
        files = z.namelist()
        plists = [x for x in files if x.startswith("Payload/") and x.count("/") == 2 and x.endswith(".app/Info.plist")]
        if len(plists) != 1:
            raise ValueError("Expected exactly one Payload/*.app/Info.plist")
        meta = plistlib.loads(z.read(plists[0]))
        bundle = plists[0].rsplit("/", 1)[0]
        executable = meta.get("CFBundleExecutable")
        if not executable or bundle + "/" + executable not in files:
            raise ValueError("Main executable missing")
        main = inspect(z.read(bundle + "/" + executable))
        embedded = [x for x in files if x == bundle + "/Frameworks/" + expected
                    or (x.startswith(bundle + "/Frameworks/") and x.endswith("/" + expected))]
        referenced = any(x in main["linked_libraries"] for x in
                         ("@rpath/" + expected, "@executable_path/Frameworks/" + expected))
        return {
            "bundle_identifier": meta.get("CFBundleIdentifier"),
            "executable": executable,
            "cpu": main["architecture"],
            "main_is_encrypted": main["encrypted"],
            "linked_from_main_executable": referenced,
            "embedded_library_paths": embedded,
            "library_expected": expected,
            "main_rpaths": main["rpaths"],
            "main_linked_libraries": main["linked_libraries"],
            "signature_resources_present": bundle + "/_CodeSignature/CodeResources" in files,
            "on_device_runtime_loading_verified": False,
            "interpretation": "Presence and Mach-O linkage are static checks. They cannot prove the library was actually loaded by iOS."
        }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    parser.add_argument("--library", default="EMReadOnlyDiagnostics.dylib")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.ipa, args.library)
    report = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report)

if __name__ == "__main__":
    main()
