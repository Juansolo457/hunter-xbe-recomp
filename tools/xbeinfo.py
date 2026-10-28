"""Print an original Xbox XBE's header: hash, title, entry, sections and XDK library builds.

    python -I tools/xbeinfo.py <default.xbe>

Read-only; stdlib only. The library builds decide which sdk/xdk/<build> set xbe_symbols needs.
"""
import datetime
import hashlib
import struct
import sys

ENTRY_KEYS = {'retail': 0xA8FC57AB, 'debug': 0x94859D4B}
THUNK_KEYS = {'retail': 0x5B6D40B6, 'debug': 0xEFB1F152}
SECTION_FLAGS = {1: 'W', 2: 'preload', 4: 'X', 8: 'head-page-ro', 16: 'tail-page-ro'}


def when(t):
    return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def cstr(data, off):
    return data[off:data.index(b'\0', off)].decode('latin-1')


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    d = open(sys.argv[1], 'rb').read()
    if d[:4] != b'XBEH':
        sys.exit('not an XBE (no XBEH magic)')
    (base, _hdr, _img, _imghdr, stamp, cert, nsec, sec, _init, entry, tls) = \
        struct.unpack_from('<' + 'I' * 11, d, 0x104)
    dbg_name = struct.unpack_from('<I', d, 0x150)[0]
    kthunk = struct.unpack_from('<I', d, 0x158)[0]
    nlib, lib = struct.unpack_from('<II', d, 0x160)

    print(f'size     {len(d)}')
    print(f'sha1     {hashlib.sha1(d).hexdigest()}')
    print(f'base     {base:#010x}   image built {when(stamp)}')
    for kind in ('retail', 'debug'):
        print(f'entry    {entry ^ ENTRY_KEYS[kind]:#010x} ({kind} key)   '
              f'kernel thunk {kthunk ^ THUNK_KEYS[kind]:#010x}')
    print(f'tls      {tls:#010x}')
    if dbg_name:
        print(f'debug    {cstr(d, dbg_name - base)}')

    c = cert - base
    cert_time, title_id = struct.unpack_from('<II', d, c + 4)
    title = d[c + 12:c + 92].decode('utf-16-le').split('\0')[0]
    media, region, _rating, _disk, version = struct.unpack_from('<IIIII', d, c + 0x9C)
    print(f"title    '{title}'  id {title_id:08X}  region {region:#x}  media {media:#x}  "
          f'version {version}  certified {when(cert_time)}')

    print('sections:')
    for i in range(nsec):
        o = sec - base + i * 56
        flags, va, vsize, raw, rawsize, name = struct.unpack_from('<IIIIII', d, o)
        names = ','.join(n for bit, n in SECTION_FLAGS.items() if flags & bit)
        print(f'  {cstr(d, name - base):<10} va {va:#010x} vsize {vsize:#09x} '
              f'raw {raw:#09x} rawsize {rawsize:#09x}  {names}')

    print('libraries:')
    for i in range(nlib):
        o = lib - base + i * 16
        name = d[o:o + 8].rstrip(b'\0').decode('latin-1')
        major, minor, build, flags = struct.unpack_from('<HHHH', d, o + 8)
        print(f'  {name:<8} {major}.{minor}.{build}  flags {flags:#06x}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
