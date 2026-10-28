"""Disassemble a function of an XBE, naming known addresses.

    python tools/xbedis.py assets/default.xbe <hex address or name> [count]

Names come from name<TAB>0xADDR files in the current folder (cfgsyms.tsv, oovpa.tsv, oovpa2.tsv:
oovpa_scan.py output and the config's symbols). Needs capstone (pip install capstone), so run it
without -I if capstone is a user-site package. Read-only.
"""
import struct
import sys

import capstone


def sections(d):
    base = struct.unpack_from('<I', d, 0x104)[0]
    nsec, sec = struct.unpack_from('<II', d, 0x11C)
    out = []
    for i in range(nsec):
        _fl, va, vsz, raw, rsz, _nm = struct.unpack_from('<IIIIII', d, sec - base + i * 56)
        out.append((va, raw, rsz))
    return out


def fo(secs, va):
    for sva, raw, rsz in secs:
        if sva <= va < sva + rsz:
            return raw + va - sva
    raise SystemExit(f'{va:#x} is not in a section')


def names():
    table = {}
    for path in ('cfgsyms.tsv', 'oovpa.tsv', 'oovpa2.tsv'):
        try:
            for line in open(path):
                n, a = line.split('\t')[:2]
                table[n] = int(a, 16)
        except FileNotFoundError:
            pass
    return table


def main():
    d = open(sys.argv[1], 'rb').read()
    secs = sections(d)
    target = sys.argv[2]
    table = names()
    va = table[target] if target in table else int(target, 16)
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    off = fo(secs, va)
    rev = {v: k for k, v in table.items()}
    n = 0
    for ins in md.disasm(d[off:off + 4096], va):
        note = ''
        for tok in ins.op_str.replace('[', ' ').replace(']', ' ').replace(',', ' ').split():
            if tok.startswith('0x'):
                v = int(tok, 16)
                if v in rev:
                    note = '  ; ' + rev[v]
        print(f'{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}{note}')
        n += 1
        if n >= count or (ins.mnemonic == 'ret' and count == 40):
            break


if __name__ == '__main__':
    main()
