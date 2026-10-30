"""Read an original Xbox disc image (XDVDFS / XISO): list it, or extract it.

    python -I tools/xiso.py <image.iso> list
    python -I tools/xiso.py <image.iso> extract <outdir> [path ...]

`extract` with no paths writes the whole disc; with paths (as `list` prints them, the leading
slash optional: default.xbe, Media/Menu.JAM) only those. Works on an XISO (filesystem at offset 0) and on a full disc dump
(game partition further in). Read-only on the image; stdlib only.
"""
import os
import struct
import sys

SECTOR = 2048
MAGIC = b'MICROSOFT*XBOX*MEDIA'
# where the game partition starts: XISO, and the full-disc layouts of the Xbox's discs
PARTITION_OFFSETS = (0, 0x18300000, 0xFD90000, 0x2080000, 0x10000)
ATTR_DIRECTORY = 0x10


def find_partition(f):
    for off in PARTITION_OFFSETS:
        f.seek(off + 32 * SECTOR)
        if f.read(len(MAGIC)) == MAGIC:
            return off
    sys.exit('not an Xbox disc image: no XDVDFS volume descriptor found')


def walk(f, base, sector, size, prefix, out):
    """(path, start sector, size) of every file under a directory table."""
    if size == 0:
        return
    f.seek(base + sector * SECTOR)
    table = f.read(size)
    stack = [0]
    seen = set()
    while stack:
        off = stack.pop()
        if off in seen or off + 14 > len(table):
            continue
        seen.add(off)
        left, right, start, length, attr, name_len = struct.unpack_from('<HHIIBB', table, off)
        if left == 0xFFFF:  # padding
            continue
        name = table[off + 14:off + 14 + name_len].decode('latin-1')
        path = f'{prefix}/{name}'
        if attr & ATTR_DIRECTORY:
            walk(f, base, start, length, path, out)
        else:
            out.append((path, start, length))
        if right:
            stack.append(right * 4)
        if left:
            stack.append(left * 4)


def key(path):
    """A disc path to compare: case-insensitive, either slash, leading slash optional (Git Bash
    turns a leading / into a Windows path, so `Media/Menu.JAM` is the portable spelling)."""
    return path.replace('\\', '/').strip('/').lower()


def safe_join(root, path):
    full = os.path.normpath(os.path.join(root, *path.strip('/').split('/')))
    if not full.startswith(os.path.normpath(root) + os.sep):
        sys.exit(f'refusing a path outside the output folder: {path}')
    return full


def main():
    if len(sys.argv) < 3 or sys.argv[2] not in ('list', 'extract'):
        sys.exit(__doc__)
    image, command = sys.argv[1], sys.argv[2]
    with open(image, 'rb') as f:
        base = find_partition(f)
        f.seek(base + 32 * SECTOR + len(MAGIC))
        root_sector, root_size = struct.unpack('<II', f.read(8))
        files = []
        walk(f, base, root_sector, root_size, '', files)
        files.sort()
        if command == 'list':
            print(f'partition at {base:#x}, {len(files)} files, '
                  f'{sum(s for _, _, s in files) / 1e6:.1f} MB')
            for path, _, size in files:
                print(f'{size:>12} {path}')
            return 0
        if len(sys.argv) < 4:
            sys.exit(__doc__)
        outdir = os.path.abspath(sys.argv[3])
        wanted = {key(p) for p in sys.argv[4:]}
        written = 0
        for path, start, size in files:
            if wanted and key(path) not in wanted:
                continue
            dst = safe_join(outdir, path)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            f.seek(base + start * SECTOR)
            with open(dst, 'wb') as o:
                left = size
                while left > 0:
                    chunk = f.read(min(left, 1 << 22))
                    if not chunk:
                        sys.exit(f'image ends inside {path}')
                    o.write(chunk)
                    left -= len(chunk)
            written += 1
        missing = wanted - {key(p) for p, _, _ in files}
        print(f'extracted {written} files into {outdir}')
        if missing:
            print('not on the disc: ' + ', '.join(sorted(missing)))
            return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
