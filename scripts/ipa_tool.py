#!/usr/bin/env python3
"""Dependency-free IPA creator, validator and streaming repacker for Linux builds."""
import argparse
import os
import pathlib
import plistlib
import shutil
import stat
import sys
import tempfile
import zipfile

MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
AUTO_STORE_THRESHOLD = 8 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


def _safe_archive_path(name):
    path = pathlib.PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError("unsafe archive path: " + name)
    return path


def _app_info(entries, archive):
    app_plists = [
        item for item in entries
        if len(_safe_archive_path(item.filename).parts) == 3
        and item.filename.startswith("Payload/")
        and item.filename.endswith(".app/Info.plist")
    ]
    if len(app_plists) != 1:
        raise ValueError("expected exactly one Payload/*.app/Info.plist")
    info_item = app_plists[0]
    metadata = plistlib.loads(archive.read(info_item))
    bundle_id = metadata.get("CFBundleIdentifier")
    executable = metadata.get("CFBundleExecutable")
    if not bundle_id:
        raise ValueError("CFBundleIdentifier missing")
    if not executable or "/" in executable or executable in {".", ".."}:
        raise ValueError("CFBundleExecutable missing or unsafe")
    app_dir = info_item.filename.rsplit("/", 1)[0]
    names = {item.filename for item in entries}
    executable_path = app_dir + "/" + executable
    if executable_path not in names:
        raise ValueError("app executable missing")
    executable_item = next(item for item in entries if item.filename == executable_path)
    if executable_item.file_size == 0:
        raise ValueError("app executable is empty")
    return metadata, app_dir, executable_path


def _validate_symlinks(entries, archive, app_dir):
    root = pathlib.PurePosixPath(app_dir)
    for item in entries:
        mode = item.external_attr >> 16
        if not stat.S_ISLNK(mode):
            continue
        path = _safe_archive_path(item.filename)
        target = archive.read(item).decode("utf-8")
        target_path = pathlib.PurePosixPath(target)
        if target_path.is_absolute():
            raise ValueError("absolute symlink in IPA: " + item.filename)
        resolved = pathlib.PurePosixPath(os.path.normpath(str(path.parent / target_path)))
        if resolved != root and root not in resolved.parents:
            raise ValueError("symlink escapes app bundle: " + item.filename)


def validate(ipa):
    with zipfile.ZipFile(ipa) as archive:
        entries = archive.infolist()
        if not entries:
            raise ValueError("empty IPA")
        total = 0
        seen = set()
        for item in entries:
            _safe_archive_path(item.filename)
            if item.filename in seen:
                raise ValueError("duplicate archive path: " + item.filename)
            seen.add(item.filename)
            total += item.file_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("uncompressed IPA exceeds 4 GiB limit")
        metadata, app_dir, executable = _app_info(entries, archive)
        _validate_symlinks(entries, archive, app_dir)
        broken_entry = archive.testzip()
        if broken_entry is not None:
            raise ValueError("ZIP CRC check failed: " + broken_entry)
        print(
            "VALID", ipa,
            "bundle:", metadata["CFBundleIdentifier"],
            "executable:", executable.rsplit("/", 1)[-1],
            "minimum iOS:", metadata.get("MinimumOSVersion", "unspecified"),
            "entries:", len(entries),
            "uncompressed bytes:", total,
        )
        return entries


def _write_entry(archive, source_path, archive_name, compression):
    item = zipfile.ZipInfo(archive_name, date_time=(1980, 1, 1, 0, 0, 0))
    item.create_system = 3
    mode = source_path.lstat().st_mode
    item.external_attr = (mode & 0o777) << 16
    if stat.S_ISDIR(mode):
        item.filename += "/"
        item.external_attr = ((stat.S_IFDIR | (mode & 0o777)) << 16) | 0x10
        item.compress_type = zipfile.ZIP_STORED
        archive.writestr(item, b"")
        return
    if stat.S_ISLNK(mode):
        item.external_attr = (stat.S_IFLNK | (mode & 0o777)) << 16
        item.compress_type = zipfile.ZIP_STORED
        archive.writestr(item, os.readlink(source_path).encode("utf-8"))
        return
    if not stat.S_ISREG(mode):
        raise ValueError("unsupported special file in app bundle: " + str(source_path))
    size = source_path.stat().st_size
    item.compress_type = (
        zipfile.ZIP_STORED
        if compression == "store" or (compression == "auto" and size >= AUTO_STORE_THRESHOLD)
        else zipfile.ZIP_DEFLATED
    )
    if item.compress_type == zipfile.ZIP_DEFLATED:
        item._compresslevel = 1
    with source_path.open("rb") as source, archive.open(item, "w", force_zip64=True) as target:
        shutil.copyfileobj(source, target, length=CHUNK_SIZE)


def create(app, output, compression="auto"):
    app = pathlib.Path(app).resolve(strict=True)
    if not app.is_dir() or app.suffix != ".app":
        raise ValueError("input must be an existing .app directory")
    try:
        output_resolved = pathlib.Path(output).resolve()
        output_resolved.relative_to(app)
    except ValueError:
        pass
    else:
        raise ValueError("IPA output must be outside the app bundle")

    info_path = app / "Info.plist"
    if not info_path.is_file():
        raise ValueError("app bundle is missing Info.plist")
    with info_path.open("rb") as stream:
        metadata = plistlib.load(stream)
    bundle_id = metadata.get("CFBundleIdentifier")
    executable = metadata.get("CFBundleExecutable")
    if not bundle_id:
        raise ValueError("CFBundleIdentifier missing from Info.plist")
    if not executable or "/" in executable or executable in {".", ".."}:
        raise ValueError("CFBundleExecutable missing or unsafe in Info.plist")
    executable_path = app / executable
    if not executable_path.is_file() or executable_path.stat().st_size == 0:
        raise ValueError("app executable missing or empty: " + executable)
    if not os.access(executable_path, os.X_OK):
        raise ValueError("app executable is not marked executable: " + executable)

    files = [app]
    for current, directories, names in os.walk(app, followlinks=False):
        current_path = pathlib.Path(current)
        directories.sort()
        names.sort()
        for name in list(directories):
            path = current_path / name
            if path.is_symlink():
                files.append(path)
                directories.remove(name)
            else:
                files.append(path)
        files.extend(current_path / name for name in names)
    files.sort(key=lambda path: (path != app, path.relative_to(app).as_posix()))
    total = 0
    for path in files:
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            total += path.stat().st_size
        elif not (stat.S_ISDIR(mode) or stat.S_ISLNK(mode)):
            raise ValueError("unsupported special file in app bundle: " + str(path))
    if total > MAX_TOTAL_BYTES:
        raise ValueError("app bundle exceeds 4 GiB uncompressed limit")

    output = pathlib.Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output = output.resolve()
    handle, temp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=output.parent)
    os.close(handle)
    try:
        with zipfile.ZipFile(temp_name, "w", allowZip64=True) as archive:
            for path in files:
                relative = path.relative_to(app.parent).as_posix()
                _write_entry(archive, path, "Payload/" + relative, compression)
        validate(pathlib.Path(temp_name))
        os.replace(temp_name, output)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    print("OUTPUT", output, "bytes:", output.stat().st_size, "unsigned: yes")


def repackage(ipa, output):
    validate(ipa)
    output.mkdir(parents=True, exist_ok=True)
    target = output / (ipa.stem + "-repacked-unsigned.ipa")
    with zipfile.ZipFile(ipa, "r") as source, zipfile.ZipFile(target, "w", allowZip64=True) as dest:
        for original in source.infolist():
            copied = zipfile.ZipInfo(original.filename, original.date_time)
            copied.comment = original.comment
            copied.extra = original.extra
            copied.internal_attr = original.internal_attr
            copied.external_attr = original.external_attr
            copied.compress_type = original.compress_type
            copied.create_system = original.create_system
            copied.create_version = original.create_version
            copied.extract_version = original.extract_version
            copied.flag_bits = original.flag_bits
            copied.volume = original.volume
            copied.file_size = original.file_size
            copied._compresslevel = 1
            if original.is_dir():
                dest.writestr(copied, b"")
            else:
                with source.open(original, "r") as src, dest.open(copied, "w", force_zip64=True) as dst:
                    shutil.copyfileobj(src, dst, length=CHUNK_SIZE)
    validate(target)
    print("OUTPUT", target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["create", "validate", "repackage"])
    parser.add_argument("input", type=pathlib.Path, help=".app directory for create; .ipa file otherwise")
    parser.add_argument("--output", type=pathlib.Path)
    parser.add_argument("--compression", choices=["auto", "deflate", "store"], default="auto")
    args = parser.parse_args()

    if args.mode == "create":
        output = args.output or pathlib.Path("output") / (args.input.stem + ".ipa")
        create(args.input, output, args.compression)
        return
    if not args.input.is_file():
        raise ValueError("input IPA does not exist: " + str(args.input))
    output = args.output or pathlib.Path("output")
    if args.mode == "repackage":
        repackage(args.input, output)
    else:
        validate(args.input)
        output.mkdir(parents=True, exist_ok=True)
        report = output / "validation.txt"
        report.write_text("IPA archive structure and ZIP integrity validated: " + args.input.name + "\n")
        print("OUTPUT", report)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, zipfile.BadZipFile, OSError, plistlib.InvalidFileException, UnicodeDecodeError) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
