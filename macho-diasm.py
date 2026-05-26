#!/usr/bin/env python3
import sys
import struct
import subprocess
from pathlib import Path

try:
    from capstone import Cs, CS_ARCH_X86, CS_ARCH_ARM64, CS_MODE_64, CS_MODE_ARM
except ImportError:
    Cs = None


MH_MAGIC_64 = 0xFEEDFACF
MH_CIGAM_64 = 0xCFFAEDFE
FAT_MAGIC = 0xCAFEBABE
FAT_CIGAM = 0xBEBAFECA

CPU_X86_64 = 0x01000007
CPU_ARM64 = 0x0100000C

LC_SEGMENT_64 = 0x19


def read_u32(data, off, endian="<"):
    return struct.unpack_from(endian + "I", data, off)[0]


def parse_fat(data):
    magic = read_u32(data, 0, ">")
    if magic not in (FAT_MAGIC, FAT_CIGAM):
        return [(0, len(data))]

    nfat = read_u32(data, 4, ">")
    arches = []

    off = 8
    for _ in range(nfat):
        cputype, cpusubtype, offset, size, align = struct.unpack_from(">IIIII", data, off)
        arches.append((offset, size, cputype))
        off += 20

    return [(offset, size) for offset, size, _ in arches]


def parse_macho64(data, base_offset=0):
    magic = read_u32(data, base_offset, "<")

    if magic == MH_MAGIC_64:
        endian = "<"
    elif magic == MH_CIGAM_64:
        endian = ">"
    else:
        raise ValueError("Not a 64-bit Mach-O file")

    header = struct.unpack_from(endian + "IiiIIII", data, base_offset)
    _, cputype, cpusubtype, filetype, ncmds, sizeofcmds, flags = header

    reserved = read_u32(data, base_offset + 28, endian)
    cmd_off = base_offset + 32

    sections = []

    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from(endian + "II", data, cmd_off)

        if cmd == LC_SEGMENT_64:
            segname = data[cmd_off + 8:cmd_off + 24].rstrip(b"\x00").decode(errors="ignore")
            vmaddr, vmsize, fileoff, filesize, maxprot, initprot, nsects, flags = struct.unpack_from(
                endian + "QQQQiiII", data, cmd_off + 24
            )

            sect_off = cmd_off + 72

            for _ in range(nsects):
                sectname = data[sect_off:sect_off + 16].rstrip(b"\x00").decode(errors="ignore")
                s_segname = data[sect_off + 16:sect_off + 32].rstrip(b"\x00").decode(errors="ignore")

                addr, size, offset, align, reloff, nreloc, flags, reserved1, reserved2, reserved3 = struct.unpack_from(
                    endian + "QQIIIIIIII", data, sect_off + 32
                )

                sections.append({
                    "segment": s_segname,
                    "section": sectname,
                    "addr": addr,
                    "size": size,
                    "offset": offset,
                    "flags": flags,
                })

                sect_off += 80

        cmd_off += cmdsize

    return cputype, sections


def disassemble(code, addr, cputype):
    if Cs is None:
        print("[!] Capstone not installed. Falling back to otool suggestion.")
        return

    if cputype == CPU_X86_64:
        md = Cs(CS_ARCH_X86, CS_MODE_64)
    elif cputype == CPU_ARM64:
        md = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    else:
        print(f"[!] Unsupported CPU type: {hex(cputype)}")
        return

    for insn in md.disasm(code, addr):
        print(f"0x{insn.address:016x}: {insn.mnemonic:<8} {insn.op_str}")


def analyze(path):
    path = Path(path)
    data = path.read_bytes()

    slices = parse_fat(data)

    for index, (offset, size) in enumerate(slices):
        print(f"\n=== Mach-O slice {index} offset={offset} size={size} ===")

        try:
            cputype, sections = parse_macho64(data, offset)
        except Exception as e:
            print(f"[!] Skipping slice: {e}")
            continue

        print(f"CPU: {hex(cputype)}")

        text = None

        for s in sections:
            print(
                f"{s['segment']},{s['section']} "
                f"addr=0x{s['addr']:x} "
                f"size=0x{s['size']:x} "
                f"fileoff=0x{s['offset']:x}"
            )

            if s["segment"] == "__TEXT" and s["section"] == "__text":
                text = s

        if not text:
            print("[!] No __TEXT,__text section found.")
            continue

        start = text["offset"]
        end = start + text["size"]
        code = data[start:end]

        print("\n--- Disassembly: __TEXT,__text ---")
        disassemble(code, text["addr"], cputype)


def otool_fallback(path):
    print("\n--- otool fallback ---")
    subprocess.run(["otool", "-tvV", path])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python3 macho_disasm.py /path/to/binary")
        print("example: python3 macho_disasm.py /Applications/Calculator.app/Contents/MacOS/Calculator")
        sys.exit(1)

    target = sys.argv[1]

    try:
        analyze(target)
    except Exception as e:
        print(f"[!] Python parser failed: {e}")
        otool_fallback(target)
