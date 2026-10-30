"""Disassemble a function of an XBE, naming known addresses.

    python -m venv .venv-tools && .venv-tools/Scripts/pip install capstone   (once, outside the repo)
    .venv-tools/Scripts/python -I tools/xbedis.py assets/default.xbe <hex address or name> [count]

Names come from name<TAB>0xADDR files in the current folder (cfgsyms.tsv, oovpa.tsv, oovpa2.tsv:
oovpa_scan.py output and the config's symbols). Needs capstone: install it in a virtual environment
and run that interpreter with -I, which still loads the environment's own packages but no user-site
ones. Without a count it stops at the first ret or after 40 instructions. Read-only.
"""
import argparse
import struct

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
    ap = argparse.ArgumentParser(description='Disassemble a function of an XBE, naming known addresses.')
    ap.add_argument('xbe')
    ap.add_argument('target', help='hex address or a name from the .tsv files')
    ap.add_argument('count', nargs='?', type=int, help='instructions to print (default: to the first ret, at most 40)')
    args = ap.parse_args()
    table = names()
    if args.target in table:
        va = table[args.target]
    else:
        try:
            va = int(args.target, 16)
        except ValueError:
            ap.error(f'{args.target!r} is neither a known name nor a hex address')
    if args.count is not None and args.count < 0:
        ap.error('count must be 0 or more')
    to_ret = args.count is None
    count = 40 if to_ret else args.count
    d = open(args.xbe, 'rb').read()
    secs = sections(d)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    off = fo(secs, va)
    rev = {v: k for k, v in table.items()}
    n = 0
    if count == 0:
        return
    for ins in md.disasm(d[off:off + 4096], va):
        note = ''
        for tok in ins.op_str.replace('[', ' ').replace(']', ' ').replace(',', ' ').split():
            if tok.startswith('0x'):
                v = int(tok, 16)
                if v in rev:
                    note = '  ; ' + rev[v]
        print(f'{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic} {ins.op_str}{note}')
        n += 1
        if n >= count or (ins.mnemonic == 'ret' and to_ret):
            break


if __name__ == '__main__':
    main()
