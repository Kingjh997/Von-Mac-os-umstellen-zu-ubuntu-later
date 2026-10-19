#!/usr/bin/env python3
"""Verify the resulting binary really is an arm64 Mach-O dynamic library."""
import pathlib
import struct
import sys

MH_MAGIC_64 = 0xFEEDFACF
CPU_TYPE_ARM64 = 0x0100000C
MH_DYLIB = 6


def validate(file_path: pathlib.Path) -> None:
    binary = file_path.read_bytes()
    if len(binary) < 32:
        raise ValueError("Binary too small for Mach-O header")
    magic, cpu, subtype, filetype, command_count, command_size, flags, reserved = (
        struct.unpack_from("<IiiIIIII", binary, 0)
    )
    if magic != MH_MAGIC_64:
        raise ValueError(f"Not a thin 64-bit Mach-O binary (magic={magic:#x})")
    if cpu != CPU_TYPE_ARM64:
        raise ValueError(f"Wrong CPU type: {cpu:#x} (expected arm64)")
    if filetype != MH_DYLIB:
        raise ValueError(f"Wrong Mach-O type: {filetype} (expected dylib)")
    if 32 + command_size > len(binary):
        raise ValueError("Truncated Mach-O load commands")
    print(f"PASS {file_path}: Mach-O arm64 dylib, {command_count} load commands")


if __name__ == "__main__":
    try:
        validate(pathlib.Path(sys.argv[1]))
    except (IndexError, OSError, ValueError, struct.error) as err:
        print(f"FAIL: {err}", file=sys.stderr)
        sys.exit(1)
