#!/usr/bin/env python3
"""Compare iOS SDK and arm64 Mach-O facts across independent CI runners."""
import argparse,json,os,hashlib,subprocess
from pathlib import Path
from macho_audit import inspect
def run(*args):
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=15)
        return (p.stdout+p.stderr).strip().splitlines()[0]
    except (OSError,IndexError,subprocess.TimeoutExpired):return "unavailable"
def probe(sdk):
    root=Path(sdk)/"System/Library/Frameworks"
    frameworks={}
    for name in ("Foundation","UIKit","WebKit","QuartzCore","Security","StoreKit","GameKit"):
        d=root/(name+".framework")
        frameworks[name]={"header":(d/"Headers"/(name+".h")).is_file(),"stub":bool(list(d.glob("*.tbd")))}
    return {"sdk_name":Path(sdk).name,"frameworks":frameworks}
def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="mode",required=True)
    c=sub.add_parser("collect")
    c.add_argument("--os",required=True)
    c.add_argument("--sdk",type=Path,required=True)
    c.add_argument("--binary",type=Path,required=True)
    c.add_argument("--output",type=Path,required=True)
    d=sub.add_parser("compare")
    d.add_argument("--macos",type=Path,required=True)
    d.add_argument("--ubuntu",type=Path,required=True)
    d.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.mode=="collect":
        result={"runner":a.os,"commit":os.environ.get("GITHUB_SHA"),
            "theos_revision":run("git","-C",os.environ.get("THEOS","/missing"),"rev-parse","HEAD"),
            "clang":run("clang","--version"),"xcode":run("xcodebuild","-version"),
            "apple_clang":run("xcrun","--sdk","iphoneos","clang","--version") if a.os=="macos" else None,
            "sdk":probe(a.sdk),
            "source_hash":hashlib.sha256(Path("tweak/Tweak.xm").read_bytes()).hexdigest(),
            "makefile_hash":hashlib.sha256(Path("tweak/Makefile").read_bytes()).hexdigest(),
            "binary":inspect(a.binary.read_bytes())}
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(result,indent=2)+"\n")
        if not result["binary"]["valid_arm64_dylib"]:raise SystemExit("Bad arch")
    else:
        m=json.loads(a.macos.read_text());u=json.loads(a.ubuntu.read_text())
        checks={"same_commit":m["commit"]==u["commit"],
                "same_source":m["source_hash"]==u["source_hash"],
                "same_makefile":m["makefile_hash"]==u["makefile_hash"],
                "same_install_name":m["binary"]["install_names"]==u["binary"]["install_names"],
                "same_min_ios":m["binary"]["min_os"]==u["binary"]["min_os"],
                "both_arm64":m["binary"]["valid_arm64_dylib"] and u["binary"]["valid_arm64_dylib"],
                "no_substrate":not(m["binary"]["external_hook_dependencies"] or u["binary"]["external_hook_dependencies"]),
                "same_dynamic_dependencies":sorted(m["binary"]["linked_libraries"])==sorted(u["binary"]["linked_libraries"])}
        lines=["# Mac Xcode vs Ubuntu Theos: derselbe Test-Quellcode","",
        "| Merkmal | macOS | Ubuntu |","|---|---|---|"]
        for key in ("clang","theos_revision"):
            lines.append(f"| {key} | {m[key]} | {u[key]} |")
        for key in ("sdk_name",):
            lines.append(f'| {key} | {m["sdk"][key]} | {u["sdk"][key]} |')
        for key in ("sdk_version","min_os","architecture","install_names","linked_libraries","rpaths"):
            lines.append(f'| {key} | {m["binary"][key]} | {u["binary"][key]} |')
        lines+=["","## Prüfungen"]+[f'- {key}: {value}' for key,value in checks.items()]
        lines+=["","## SDK Header/Stubs (macOS, Ubuntu)"]
        for name in m["sdk"]["frameworks"]:
            lines.append(f'- {name}: {m["sdk"]["frameworks"][name]} / {u["sdk"]["frameworks"][name]}')
        lines+=["","Wichtig: Keine iPhone-Laufzeitmessung. Kein Nachbau von Lab-/EM-Menüs. Ein unterschiedliches SDK verändert keinen hartkodierten UI-Text.",""]
        a.output.mkdir(parents=True,exist_ok=True)
        (a.output/"comparison.md").write_text("\n".join(lines))
        (a.output/"comparison.json").write_text(json.dumps({"checks":checks,"macos":m,"ubuntu":u},indent=2)+"\n")
        if not all(list(checks.values())[:7]):raise SystemExit("Critical build mismatch")
if __name__=="__main__":main()
