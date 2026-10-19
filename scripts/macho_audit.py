#!/usr/bin/env python3
"""Read-only thin ARM64 Mach-O loader audit. Does NOT prove runtime execution."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

def v(num):
    return f"{num >> 16}.{(num >> 8) & 255}.{num & 255}"

def inspect(binary):
    if len(binary) < 32 or struct.unpack_from("<I", binary)[0] != 0xfeedfacf:
        raise ValueError("Expected thin little-endian Mach-O 64")
    magic, cpu, subtype, kind, count, commands, flags, reserved = struct.unpack_from("<IiiIIIII", binary)
    if 32 + commands > len(binary) or count > 2000:
        raise ValueError("Malformed Mach-O load commands")
    out = dict(
        size_bytes=len(binary), sha256=hashlib.sha256(binary).hexdigest(),
        architecture="arm64" if cpu == 0x0100000c else hex(cpu),
        file_type="dylib" if kind == 6 else f"Mach-O type {kind}",
        install_names=[], linked_libraries=[], rpaths=[],
        min_os=None, sdk_version=None, platform_number=None,
        code_signature_present=False, encrypted=False,
    )
    pos = 32
    for _ in range(count):
        if pos + 8 > 32 + commands:
            raise ValueError("Missing load command")
        cmd, size = struct.unpack_from("<II", binary, pos)
        if size < 8 or pos + size > 32 + commands:
            raise ValueError("Invalid load command size")
        base = cmd & 0x7fffffff
        if base in (0xc, 0xd, 0x18, 0x1f, 0x23, 0x20):
            if size < 24:
                raise ValueError("Truncated dylib command")
            offset = struct.unpack_from("<I", binary, pos + 8)[0]
            if not 24 <= offset < size:
                raise ValueError("Invalid dylib name offset")
            name = binary[pos + offset:pos + size].split(b"\x00", 1)[0].decode("utf8", "replace")
            out["install_names" if base == 0xd else "linked_libraries"].append(name)
        elif cmd == 0x8000001c:
            if size < 12:
                raise ValueError("Truncated rpath command")
            offset = struct.unpack_from("<I", binary, pos+8)[0]
            if not 12 <= offset < size:
                raise ValueError("Invalid rpath offset")
            out["rpaths"].append(binary[pos+offset:pos+size].split(b"\x00",1)[0].decode("utf8","replace"))
        elif cmd == 0x32 and size >= 24:
            platform, minos, sdk, tools = struct.unpack_from("<IIII", binary, pos+8)
            out.update(platform_number=platform, min_os=v(minos), sdk_version=v(sdk))
        elif cmd == 0x25 and size >= 16:
            minos, sdk = struct.unpack_from("<II", binary, pos+8)
            out.update(platform_number=2, min_os=v(minos), sdk_version=v(sdk))
        elif cmd == 0x1d:
            out["code_signature_present"] = size >= 16
        elif cmd in (0x2c, 0x21) and size >= 20:
            out["encrypted"] = struct.unpack_from("<I", binary, pos+16)[0] != 0
        pos += size
    tags = ("cydiasubstrate", "mobilesubstrate", "libhooker", "ellekit")
    out["external_hook_dependencies"] = [x for x in out["linked_libraries"] if any(t in x.lower() for t in tags)]
    out["valid_arm64_dylib"] = out["architecture"] == "arm64" and out["file_type"] == "dylib"
    return out

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--expect-install-name")
    p.add_argument("--require-arm64-dylib", action="store_true")
    a = p.parse_args()
    result = inspect(a.file.read_bytes())
    if a.output:
        a.output.parent.mkdir(parents=True, exist_ok=True)
        a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if a.require_arm64_dylib and not result["valid_arm64_dylib"]:
        raise SystemExit("Not an ARM64 dylib")
    if a.expect_install_name and result["install_names"] != [a.expect_install_name]:
        raise SystemExit("Wrong install name")
    if result["external_hook_dependencies"]:
        raise SystemExit("External jailbreak hook runtime dependency detected")

if __name__ == "__main__":
    main()
