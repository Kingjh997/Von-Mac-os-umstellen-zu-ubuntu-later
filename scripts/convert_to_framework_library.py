#!/usr/bin/env python3
"""Convert a simple Theos tweak Makefile into a standalone @rpath dylib build.

This edits only the extracted working copy of a source ZIP, not the user's ZIP.
Objective-C code with constructors works without substrate. Logos projects must
use the internal generator to avoid a Substrate runtime dependency.
"""
import argparse
import pathlib
import re
import sys

NAME = re.compile(r"(?m)^\s*TWEAK_NAME\s*[:?+]?=\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")
LIBRARY = re.compile(r"(?m)^\s*LIBRARY_NAME\s*[:?+]?=\s*([A-Za-z_][A-Za-z0-9_]*)\s*$")
TWEAK_MK = re.compile(r"(?m)^\s*include\s+\$\(THEOS_MAKE_PATH\)/tweak\.mk\s*$")
LIBRARY_MK = re.compile(r"(?m)^\s*include\s+\$\(THEOS_MAKE_PATH\)/library\.mk\s*$")


def convert(project: pathlib.Path) -> str:
    makefile = project / "Makefile"
    source = makefile.read_text(encoding="utf-8")
    if TWEAK_MK.search(source):
        matches = NAME.findall(source)
        if len(matches) != 1:
            raise ValueError("Expected one simple TWEAK_NAME = Name in Makefile")
        name = matches[0]
        source = NAME.sub("LIBRARY_NAME = " + name, source, count=1)
        source = TWEAK_MK.sub("include $(THEOS_MAKE_PATH)/library.mk", source, count=1)
    elif LIBRARY_MK.search(source):
        matches = LIBRARY.findall(source)
        if len(matches) != 1:
            raise ValueError("Expected one simple LIBRARY_NAME = Name in Makefile")
        name = matches[0]
    else:
        raise ValueError("ZIP must contain a Theos tweak.mk or library.mk project")

    if re.search(r"(?m)^\s*" + re.escape(name) + r"_LDFLAGS\b", source):
        raise ValueError(
            f"{name}_LDFLAGS already defined; adjust its install_name to "
            f"@rpath/{name}.dylib manually before uploading"
        )

    for path in project.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in (".xm", ".x"):
            continue
        code = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"%config\s*\(\s*generator\s*=\s*(?!internal\b)", code):
            raise ValueError(
                f"{path.name}: non-internal Logos generator requires a hooking "
                "runtime and is not suitable for a standalone Frameworks dylib"
            )
        if re.search(r"%hook\b", code) and not re.search(
            r"%config\s*\(\s*generator\s*=\s*internal\b", code
        ):
            path.write_text("%config(generator=internal);\n" + code, encoding="utf-8")

    source = source.rstrip() + (
        f"\n{name}_INSTALL_PATH = /usr/local/lib"
        f"\n{name}_LDFLAGS += -Wl,-install_name,@rpath/{name}.dylib\n"
    )
    makefile.write_text(source, encoding="utf-8")
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=pathlib.Path)
    args = parser.parse_args()
    try:
        print(convert(args.project))
        return 0
    except (ValueError, OSError, UnicodeError) as exc:
        print(f"Framework library conversion failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
