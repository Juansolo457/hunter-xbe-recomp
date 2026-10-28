"""List an XBE's kernel imports and check them against the SDK's kernel.

    python -I tools/xbeimports.py <default.xbe> [sdk]

Names come from sdk/runtime/kernel/ordinals.cpp; an import counts as implemented when a
KERNEL_EXPORT, KERNEL_FASTCALL or KERNEL_DATA in sdk/runtime or src/ defines its ordinal.
Exits 1 when any is missing. Read-only; stdlib only.
"""
import os
import re
import struct
import sys

THUNK_KEYS = (0x5B6D40B6, 0xEFB1F152)  # retail, debug
DEFINES = re.compile(r'KERNEL_(?:EXPORT|FASTCALL|DATA)\(\s*(\d+)\s*,')


def va_to_file(d, va):
    base = struct.unpack_from('<I', d, 0x104)[0]
    nsec, sec = struct.unpack_from('<II', d, 0x11C)
    for i in range(nsec):
        _flags, sva, vsize, raw, rawsize = struct.unpack_from('<IIIII', d, sec - base + i * 56)
        if sva <= va < sva + min(vsize, rawsize):
            return raw + va - sva
    return None


def defined_ordinals(roots):
    found = set()
    for root in roots:
        for folder, _dirs, files in os.walk(root):
            for name in files:
                if name.endswith(('.cpp', '.h')):
                    with open(os.path.join(folder, name), encoding='utf-8', errors='replace') as f:
                        found.update(int(n) for n in DEFINES.findall(f.read()))
    return found


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sdk = sys.argv[2] if len(sys.argv) == 3 else os.path.join(repo, 'sdk')
    d = open(sys.argv[1], 'rb').read()
    if d[:4] != b'XBEH':
        sys.exit('not an XBE (no XBEH magic)')
    encoded = struct.unpack_from('<I', d, 0x158)[0]
    off = None
    for key in THUNK_KEYS:
        off = va_to_file(d, encoded ^ key)
        if off is not None:
            break
    if off is None:
        sys.exit('the kernel thunk address is not inside any section')

    src = open(os.path.join(sdk, 'runtime', 'kernel', 'ordinals.cpp'), encoding='utf-8').read()
    table = src[src.index('kNames[] = {'):]
    names = [None] + re.findall(r'"(\w+)"', table[:table.index('};')])
    have = defined_ordinals([os.path.join(sdk, 'runtime'), os.path.join(repo, 'src')])

    ordinals = []
    while True:
        value = struct.unpack_from('<I', d, off)[0]
        if value == 0:
            break
        ordinals.append(value & 0x7FFFFFFF)
        off += 4
    missing = []
    for o in sorted(ordinals):
        name = names[o] if o < len(names) else '?'
        if o not in have:
            missing.append(f'{o}:{name}')
        print(f"{' ' if o in have else '!'} {o:>4} {name}")
    print(f'{len(ordinals)} kernel imports, {len(missing)} not implemented'
          + (': ' + ' '.join(missing) if missing else ''))
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
