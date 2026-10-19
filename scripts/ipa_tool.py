#!/usr/bin/env python3
"""Safe, dependency-free IPA structure validator and deterministic repacker."""
import argparse
import pathlib
import plistlib
import shutil
import sys
import zipfile

MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024

def validate(ipa):
    with zipfile.ZipFile(ipa) as archive:
        entries = archive.infolist()
        if not entries:
            raise ValueError("empty IPA")
        total = sum(item.file_size for item in entries)
        if total > MAX_TOTAL_BYTES:
            raise ValueError("uncompressed IPA exceeds 4 GiB limit")
        for item in entries:
            p = pathlib.PurePosixPath(item.filename)
            if p.is_absolute() or ".." in p.parts or "\\" in item.filename:
                raise ValueError("unsafe archive path: " + item.filename)
        app_plists = [i for i in entries if len(pathlib.PurePosixPath(i.filename).parts) == 3
                      and i.filename.startswith("Payload/") and i.filename.endswith(".app/Info.plist")]
        if len(app_plists) != 1:
            raise ValueError("expected exactly one Payload/*.app/Info.plist")
        metadata = plistlib.loads(archive.read(app_plists[0]))
        if not metadata.get("CFBundleIdentifier"):
            raise ValueError("CFBundleIdentifier missing")
        executable = metadata.get("CFBundleExecutable")
        if not executable:
            raise ValueError("CFBundleExecutable missing")
        app_dir = app_plists[0].filename.rsplit("/", 1)[0]
        if app_dir + "/" + executable not in archive.namelist():
            raise ValueError("app executable missing")
        print("VALID", ipa, "bundle:", metadata["CFBundleIdentifier"],
              "entries:", len(entries), "uncompressed bytes:", total)
        return entries

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["validate", "repackage"])
    parser.add_argument("ipa", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("output"))
    args = parser.parse_args()
    validate(args.ipa)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.mode == "repackage":
        target = args.output / (args.ipa.stem + "-repacked-unsigned.ipa")
        with zipfile.ZipFile(args.ipa) as source, zipfile.ZipFile(target, "w") as dest:
            for entry in source.infolist():
                dest.writestr(entry, source.read(entry))
        validate(target)
        print("OUTPUT", target)
    else:
        report = args.output / "validation.txt"
        report.write_text("IPA archive structure validated: " + args.ipa.name + "\n")
        print("OUTPUT", report)

if __name__ == "__main__":
    try:
        main()
    except (ValueError, zipfile.BadZipFile, OSError, plistlib.InvalidFileException) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
