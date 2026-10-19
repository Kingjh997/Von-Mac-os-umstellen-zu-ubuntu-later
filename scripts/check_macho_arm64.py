#!/usr/bin/env python3
"""Validate a thin arm64 Mach-O dylib and optional Frameworks compatibility."""
import argparse
import pathlib
import struct
import sys

MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
MH_DYLIB = 6
LC_ID_DYLIB = 0xD
LC_LOAD_DYLIBS = {0xC, 0x18, 0x1F, 0x23}


def dylib_name(buf: bytes, pos: int, size: int) -> str:
    if size < 24:
        raise ValueError("Malformed dylib load command")
    offset = struct.unpack_from("<I", buf, pos + 8)[0]
    if offset < 24 or offset >= size:
        raise ValueError("Invalid dylib name offset")
    data = buf[pos + offset:pos + size].split(b"\x00", 1)[0]
    return data.decode("utf-8", errors="replace")


def validate(path: pathlib.Path, framework_name: str | None = None) -> None:
    data = path.read_bytes()
    if len(data) < 32:
        raise ValueError("Truncated Mach-O header")
    magic, cpu, subtype, filetype, count, commands_size, flags, reserved = (
        struct.unpack_from("<IiiIIIII", data, 0)
    )
    if magic != MH_MAGIC_64 or cpu != CPU_TYPE_ARM64 or filetype != MH_DYLIB:
        raise ValueError(
            f"Not an arm64 Mach-O dylib: magic={magic:#x}, "
            f"cpu={cpu:#x}, type={filetype}"
        )
    if 32 + commands_size > len(data):
        raise ValueError("Truncated load commands")

    install_names, dependencies = [], []
    pos = 32
    end = 32 + commands_size
    for index in range(count):
        if pos + 8 > end:
            raise ValueError("Missing Mach-O load command")
        command, size = struct.unpack_from("<II", data, pos)
        if size < 8 or pos + size > end:
            raise ValueError("Malformed Mach-O load command size")
        base_cmd = command & 0x7fffffff
        if base_cmd == LC_ID_DYLIB:
            install_names.append(dylib_name(data, pos, size))
        elif base_cmd in LC_LOAD_DYLIBS:
            dependencies.append(dylib_name(data, pos, size))
        pos += size

    if framework_name is not None:
        expected_id = f"@rpath/{framework_name}.dylib"
        if install_names != [expected_id]:
            raise ValueError(
                f"Wrong dylib install name: {install_names!r}, "
                f"expected {expected_id!r}"
            )
        unwanted = [
            name for name in dependencies
            if any(tag in name.lower() for tag in (
                "cydiasubstrate", "mobilesubstrate", "libhooker", "ellekit"
            ))
        ]
        if unwanted:
            raise ValueError(
                "Frameworks dylib still depends on external tweak hooking "
                f"runtime(s): {unwanted!r}"
            )
        # Frameworks mode must not carry rootless jailbreak-only search paths.
        from macho_audit import inspect
        rootless_paths = [
            item for item in inspect(data)["rpaths"]
            if "/var/jb" in item or ".jbroot" in item or "/var/containers/Bundle/tweaksupport" in item
        ]
        if rootless_paths:
            raise ValueError(
                f"Frameworks dylib contains jailbroken-device rpaths: {rootless_paths!r}"
            )
    print(
        f"PASS {path}: arm64 dylib, {count} load commands"
        + (f", install_name={install_names[0]}" if install_names else "")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=pathlib.Path)
    parser.add_argument(
        "--frameworks-name",
        help="Require a standalone @rpath/<Name>.dylib with no external hooking runtime",
    )
    args = parser.parse_args()
    try:
        validate(args.file, args.frameworks_name)
        return 0
    except (OSError, ValueError, struct.error) as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
