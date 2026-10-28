"""Name the guest function a crash happened in, from a crash dump and the code DLL.

    python -I tools/crashsite.py out/build/release/CrashDumps/<dump>.dmp out/build/release/Hunter.dll [host address]

Reads the dump's exception record (or takes the host address given), finds the module it is in, and for
the code DLL the nearest export at or below it: the recompiled functions are exported as
__imp__sub_<guest address>. Read-only; stdlib only.
"""
import os
import struct
import sys


def streams(d):
    sig, _ver, count, rva = struct.unpack_from('<IIII', d, 0)
    if sig != 0x504D444D:
        sys.exit('not a minidump')
    for i in range(count):
        kind, size, at = struct.unpack_from('<III', d, rva + i * 12)
        yield kind, at, size


def utf16(d, rva):
    n = struct.unpack_from('<I', d, rva)[0]
    return d[rva + 4:rva + 4 + n].decode('utf-16-le')


def modules(d):
    for kind, at, _size in streams(d):
        if kind == 4:  # ModuleListStream
            n = struct.unpack_from('<I', d, at)[0]
            for i in range(n):
                base, size, _ck, _ts, name = struct.unpack_from('<QIIII', d, at + 4 + i * 108)
                yield base, size, utf16(d, name)


def exception_address(d):
    for kind, at, _size in streams(d):
        if kind == 6:  # ExceptionStream: thread id, alignment, then MINIDUMP_EXCEPTION
            code, _flags, _rec, addr = struct.unpack_from('<IIQQ', d, at + 8)
            return code, addr
    return None, None


def exports(dll):
    p = open(dll, 'rb').read()
    pe = struct.unpack_from('<I', p, 0x3C)[0]
    nsec = struct.unpack_from('<H', p, pe + 6)[0]
    opt = pe + 24
    exp_rva = struct.unpack_from('<I', p, opt + 112)[0]
    secs = []
    first = opt + struct.unpack_from('<H', p, pe + 20)[0]
    for i in range(nsec):
        vsz, va, _rsz, raw = struct.unpack_from('<IIII', p, first + i * 40 + 8)
        secs.append((va, vsz, raw))

    def off(rva):
        for va, vsz, raw in secs:
            if va <= rva < va + vsz:
                return raw + rva - va
        raise ValueError(hex(rva))

    e = off(exp_rva)
    nfun, nname, afun, aname, aord = struct.unpack_from('<IIIII', p, e + 20)
    funcs = struct.unpack_from(f'<{nfun}I', p, off(afun))
    out = []
    for i in range(nname):
        name_rva = struct.unpack_from('<I', p, off(aname) + i * 4)[0]
        ordinal = struct.unpack_from('<H', p, off(aord) + i * 2)[0]
        o = off(name_rva)
        name = p[o:p.index(b'\0', o)].decode()
        out.append((funcs[ordinal], name))
    return sorted(out)


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    d = open(sys.argv[1], 'rb').read()
    code, addr = exception_address(d)
    if len(sys.argv) > 3:
        addr = int(sys.argv[3], 16)
    print(f'exception {code:#010x} at {addr:#x}' if code is not None else f'address {addr:#x}')
    dll_name = os.path.basename(sys.argv[2]).lower()
    for base, size, name in modules(d):
        if base <= addr < base + size:
            print(f'in {name} + {addr - base:#x}')
            if os.path.basename(name).lower() == dll_name:
                rva = addr - base
                best = None
                for f_rva, f_name in exports(sys.argv[2]):
                    if f_rva <= rva:
                        best = (f_rva, f_name)
                if best:
                    print(f'nearest export {best[1]} + {rva - best[0]:#x}')
            return 0
    print('not inside any module of the dump')
    return 1


if __name__ == '__main__':
    sys.exit(main())
