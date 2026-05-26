Below is a **Python “mini Hopper”** for macOS apps using only standard Python + macOS tools.

Save as:

```bash
mini_hopper.py
```

```python
#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

OUT = Path("hopper_output")

def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        return e.output

def app_binary(path):
    p = Path(path)
    if p.suffix == ".app":
        macos = p / "Contents" / "MacOS"
        files = [x for x in macos.iterdir() if x.is_file()]
        if not files:
            raise FileNotFoundError("No binary in Contents/MacOS")
        return files[0]
    return p

def save(name, text):
    OUT.mkdir(exist_ok=True)
    file = OUT / name
    file.write_text(text, errors="ignore")
    print(f"[+] saved {file}")

def analyze(binary):
    binary = Path(binary)

    print(f"[+] Target: {binary}")

    save("01_file.txt", run(["file", str(binary)]))
    save("02_header.txt", run(["otool", "-hV", str(binary)]))
    save("03_load_commands.txt", run(["otool", "-l", str(binary)]))
    save("04_libraries.txt", run(["otool", "-L", str(binary)]))
    save("05_symbols.txt", run(["nm", "-m", str(binary)]))
    save("06_strings.txt", run(["strings", str(binary)]))
    save("07_disassembly.txt", run(["otool", "-tvV", str(binary)]))

    info = binary.parent.parent / "Info.plist"
    if info.exists():
        save("08_info_plist.txt", run(["plutil", "-p", str(info)]))

def menu():
    files = {
        "1": "01_file.txt",
        "2": "02_header.txt",
        "3": "03_load_commands.txt",
        "4": "04_libraries.txt",
        "5": "05_symbols.txt",
        "6": "06_strings.txt",
        "7": "07_disassembly.txt",
        "8": "08_info_plist.txt",
    }

    while True:
        print("""
Mini Hopper

1. File info
2. Mach-O header
3. Load commands
4. Linked libraries
5. Symbols
6. Strings
7. Disassembly
8. Info.plist
9. Search all output
0. Quit
""")

        choice = input("> ").strip()

        if choice == "0":
            break

        if choice == "9":
            q = input("Search: ").strip().lower()
            for f in OUT.glob("*.txt"):
                text = f.read_text(errors="ignore")
                for line in text.splitlines():
                    if q in line.lower():
                        print(f"{f.name}: {line}")
            continue

        file = files.get(choice)
        if not file:
            continue

        path = OUT / file
        if not path.exists():
            print("No output file.")
            continue

        text = path.read_text(errors="ignore")
        print(text[:12000])

        if len(text) > 12000:
            print("\n[truncated view, full file saved in hopper_output/]")

def main():
    if len(sys.argv) < 2:
        print("usage:")
        print("  python3 mini_hopper.py /Applications/App.app")
        print("  python3 mini_hopper.py /bin/ls")
        sys.exit(1)

    binary = app_binary(sys.argv[1])
    analyze(binary)
    menu()

if __name__ == "__main__":
    main()
```

Run:

```bash
python3 mini_hopper.py /Applications/Calculator.app
```

Or:

```bash
python3 mini_hopper.py /bin/ls
```

It creates:

```text
hopper_output/
├── 01_file.txt
├── 02_header.txt
├── 03_load_commands.txt
├── 04_libraries.txt
├── 05_symbols.txt
├── 06_strings.txt
├── 07_disassembly.txt
└── 08_info_plist.txt
```

This gives you Hopper-like basics:

```text
Mach-O header
load commands
linked dylibs/frameworks
symbols
strings
assembly
Info.plist
search
exported reports
```
