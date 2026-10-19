#!/usr/bin/env python3
"""Validate and safely unpack one trusted Theos source ZIP for Ubuntu builds.

The ZIP must contain one Theos Makefile plus package 'control', either at
the archive root or within a top-level folder.
"""
import argparse
import pathlib
import shutil
import stat
import sys
import zipfile

MAX_UNCOMPRESSED = 120 * 1024 * 1024
MAX_ENTRIES = 2000


def prepare(archive: pathlib.Path, destination: pathlib.Path) -> pathlib.Path:
    if not archive.is_file() or archive.suffix.lower() != ".zip":
        raise ValueError("Upload a .zip file in source-zips/")
    if destination.exists():
        raise ValueError("Destination already exists: " + str(destination))
    with zipfile.ZipFile(archive) as data:
        infos = data.infolist()
        if not infos or len(infos) > MAX_ENTRIES:
            raise ValueError("ZIP is empty or has too many entries")
        total = sum(entry.file_size for entry in infos)
        if total > MAX_UNCOMPRESSED:
            raise ValueError("ZIP contents exceed 120 MiB")
        seen = set()
        for entry in infos:
            name = entry.filename
            parts = pathlib.PurePosixPath(name).parts
            mode = (entry.external_attr >> 16) & 0o170000
            if (not name or name.startswith("/") or "\\" in name
                    or ".." in parts or ":" in name or "\x00" in name):
                raise ValueError("Unsafe ZIP member path: " + repr(name))
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("ZIP contains symlink or special file: " + name)
            if entry.flag_bits & 0x1:
                raise ValueError("Encrypted ZIP entries are not supported")
            relative = pathlib.Path(*parts)
            if relative in seen:
                raise ValueError("Repeated ZIP entry: " + name)
            seen.add(relative)
        destination.mkdir(parents=True)
        for entry in infos:
            target = destination.joinpath(*pathlib.PurePosixPath(entry.filename).parts)
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with data.open(entry) as input_file, target.open("wb") as output_file:
                    shutil.copyfileobj(input_file, output_file)

    candidates = [
        p.parent for p in destination.rglob("Makefile")
        if p.is_file() and (p.parent / "control").is_file()
    ]
    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one Theos project containing Makefile and control; "
            f"found {len(candidates)}"
        )
    project = candidates[0]
    if "THEOS" not in (project / "Makefile").read_text(encoding="utf-8", errors="replace"):
        raise ValueError("Makefile does not look like a Theos project")
    return project


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=pathlib.Path)
    parser.add_argument("--destination", required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = prepare(args.archive, args.destination)
        print(result)
        return 0
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        print(f"ZIP validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
