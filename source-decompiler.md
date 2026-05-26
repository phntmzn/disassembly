You can’t make a **true original-source decompiler** for macOS apps. The original Swift/Obj-C/C++ source is not inside the app binary.

But you can make a **pseudo-source decompiler** that outputs rough C-like code from disassembly.

```python id="cb8idc"
#!/usr/bin/env python3
# pseudo_decompiler.py
# stdlib only, uses macOS otool

import sys
import re
import subprocess
from pathlib import Path

def get_binary(path):
    p = Path(path)
    if p.suffix == ".app":
        macos = p / "Contents" / "MacOS"
        return next(x for x in macos.iterdir() if x.is_file())
    return p

def run_otool(binary):
    return subprocess.check_output(
        ["otool", "-tvV", str(binary)],
        text=True,
        stderr=subprocess.STDOUT
    )

def clean_symbol(line):
    return line.strip().replace(":", "")

def translate_instruction(line):
    line = line.strip()

    m = re.match(r"([0-9a-fA-F]+)\s+(.+)", line)
    if not m:
        return None

    addr, asm = m.groups()
    parts = asm.split(None, 1)
    op = parts[0]
    args = parts[1] if len(parts) > 1 else ""

    if op in ("pushq", "stp"):
        return f"// save registers: {args}"

    if op in ("popq", "ldp"):
        return f"// restore registers: {args}"

    if op in ("movq", "movl", "mov", "adrp", "add"):
        return f"{args};"

    if op in ("subq", "sub"):
        return f"// subtract {args}"

    if op in ("cmpq", "cmpl", "cmp"):
        return f"if_compare({args});"

    if op.startswith("j") or op.startswith("b."):
        return f"goto label_{args.replace('0x','')};"

    if op in ("callq", "bl"):
        return f"{args}();"

    if op in ("retq", "ret"):
        return "return;"

    if op in ("leaq", "ldr", "str"):
        return f"// memory operation: {op} {args}"

    return f"// asm: {op} {args}"

def decompile(text):
    output = []
    current_func = None

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.endswith(":") and not stripped[0:1].isdigit():
            name = clean_symbol(stripped)
            current_func = name
            output.append("")
            output.append(f"void {name}() {{")
            continue

        translated = translate_instruction(stripped)

        if translated:
            output.append(f"    {translated}")

            if translated == "return;" and current_func:
                output.append("}")
                current_func = None

    if current_func:
        output.append("}")

    return "\n".join(output)

def main():
    if len(sys.argv) < 2:
        print("usage: python3 pseudo_decompiler.py /path/to/App.app_or_binary")
        sys.exit(1)

    binary = get_binary(sys.argv[1])
    print(f"[+] binary: {binary}")

    asm = run_otool(binary)
    pseudo = decompile(asm)

    out = Path(binary.name + "_pseudo_source.c")
    out.write_text(pseudo)

    print(f"[+] wrote {out}")

if __name__ == "__main__":
    main()
```

Run:

```bash id="bn4k9n"
python3 pseudo_decompiler.py /Applications/Calculator.app
```

Output:

```text id="0vxnqu"
Calculator_pseudo_source.c
```

This will look like:

```c id="1y5m3u"
void _main() {
    // save registers
    x0, x1;
    _NSApplicationMain();
    return;
}
```

A more realistic decompiler pipeline is:

```text id="zkct92"
Mach-O binary
↓
otool disassembly
↓
symbol detection
↓
basic block detection
↓
control-flow graph
↓
pseudo-C reconstruction
↓
manual cleanup
```

Exact Swift/Objective-C source recovery is not possible unless the source code, debug symbols, or project files still exist.
