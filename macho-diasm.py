#!/usr/bin/env python3
# std_disasm.py
# No capstone. Uses macOS built-in otool.

import sys
import subprocess
from pathlib import Path

def find_app_binary(app_path: Path) -> Path:
    macos_dir = app_path / "Contents" / "MacOS"
    if not macos_dir.exists():
        raise FileNotFoundError("No Contents/MacOS folder found")

    binaries = [p for p in macos_dir.iterdir() if p.is_file()]
    if not binaries:
        raise FileNotFoundError("No executable found in Contents/MacOS")

    return binaries[0]

def disassemble(binary: Path):
    print(f"[+] Disassembling: {binary}")

    cmd = [
        "otool",
        "-tvV",   # disassemble text section, verbose
        str(binary)
    ]

    result = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if result.stderr:
        print(result.stderr)

    print(result.stdout)

def save_disassembly(binary: Path, out_file: Path):
    print(f"[+] Saving disassembly to: {out_file}")

    cmd = ["otool", "-tvV", str(binary)]

    with out_file.open("w") as f:
        subprocess.run(cmd, text=True, stdout=f, stderr=subprocess.STDOUT)

def main():
    if len(sys.argv) < 2:
        print("usage:")
        print("  python3 std_disasm.py /path/to/app_or_binary")
        print()
        print("examples:")
        print("  python3 std_disasm.py /Applications/Calculator.app")
        print("  python3 std_disasm.py /bin/ls")
        sys.exit(1)

    target = Path(sys.argv[1])

    if target.suffix == ".app":
        binary = find_app_binary(target)
    else:
        binary = target

    if not binary.exists():
        raise FileNotFoundError(binary)

    disassemble(binary)

    out_file = Path(binary.name + "_disassembly.txt")
    save_disassembly(binary, out_file)

if __name__ == "__main__":
    main()
