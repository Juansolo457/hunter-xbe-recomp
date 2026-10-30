"""Scan an XBE with XbSymbolDatabase's OOVPA patterns, read as data (no code from it runs).

    git clone https://github.com/Cxbx-Reloaded/XbSymbolDatabase <somewhere outside this repo>
    python -I tools/oovpa_scan.py <that checkout> assets/default.xbe 4361 \
        [--seed XREF_NAME=0xADDR ...] [--seed-file names.tsv ...] > oovpa.tsv

The database is MIT code with an ODbL pattern database: it is read from the checkout, never copied
here. Seeds: --seed XREF_NAME=0xADDR (for example XREF_D3D_g_pDevice=0x212E70), or --seed-file with
name<TAB>0xADDR lines. This is how config/game.toml's "oovpa <revision>" addresses were found
(docs/FINDINGS.md).

Mirrors libXbSymbolDatabase's automatic scan: per library, its sections; per symbol, every
revision tried in order and the last that matches wins (revisions above <build> only when none
at or below matches); xrefs must already be known (function addresses or derived data), derived
xrefs read as absolute dwords; passes repeat until nothing new is found. Manual scans are not
reproduced. Output: name, address, revision, matches, library.
"""
import argparse
import os
import re
import struct
import sys

UNDET, DERIVE = -1, -2
LIBS = [  # library name in the XBE, table file, sections, inl folder
    ('D3D8', 'D3D8_OOVPA.c', ('.text', 'D3D', 'FLASHROM'), 'D3D8'),
    ('DSOUND', 'DSound_OOVPA.c', ('DSOUND', '.rdata', 'FLASHROM'), 'DSound'),
    ('XAPILIB', 'Xapi_OOVPA.c', ('.text', 'XPP', 'FLASHROM'), 'Xapi'),
    ('XGRAPHC', 'XGraphic_OOVPA.c', ('.text', 'XGRPH', 'FLASHROM'), 'XGraphic'),
]


def preprocess(text):
    """Keep the branches a default build compiles: WIP_* and the like are undefined."""
    out, stack = [], []
    text = re.sub(r'/\*.*?\*/', ' ', text, flags=re.S)
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r'#\s*(ifdef|ifndef|if|else|elif|endif)\b(.*)', s)
        if m:
            kind, arg = m.group(1), m.group(2).strip()
            if kind == 'ifdef':
                stack.append([False, False])
            elif kind == 'ifndef':
                stack.append([True, True])
            elif kind == 'if':
                v = arg not in ('0',)
                stack.append([v, v])
            elif kind in ('else', 'elif'):
                top = stack[-1]
                top[0] = not top[1] if kind == 'else' else False
            elif kind == 'endif':
                stack.pop()
            continue
        if all(t[0] for t in stack):
            out.append(re.sub(r'//.*', '', line))
    return '\n'.join(out)


HEAD = re.compile(r'OOVPA_(SIG_HEADER_XREF(?:_DETECT)?|SIG_HEADER_NO_XREF(?:_DETECT)?|XREF(?:_DETECT)?|NO_XREF(?:_DETECT)?)\s*\(([^)]*)\)')
NUM = lambda t: int(t, 0)


def parse_inl(path):
    text = preprocess(open(path, encoding='utf-8', errors='replace').read())
    pats = {}
    heads = list(HEAD.finditer(text))
    for i, h in enumerate(heads):
        body = text[h.end():heads[i + 1].start() if i + 1 < len(heads) else len(text)]
        args = [a.strip() for a in h.group(2).split(',')]
        kind = h.group(1)
        name, ver = args[0], int(args[1])
        detect = 0
        if kind.endswith('_DETECT'):
            detect = {'DetectFirst': 1, 'DetectSecond': 2, 'DetectThird': 3, 'DetectFourth': 4}.get(args[-1], 0)
        xrefs, pairs = [], []
        for m in re.finditer(r'XREF_ENTRY\(\s*(0x[0-9A-Fa-f]+|\d+)\s*,\s*(\w+)\s*\)'
                             r'|OV_MATCH\(\s*([^)]*)\)'
                             r'|\{\s*(0x[0-9A-Fa-f]+|\d+)\s*,\s*(0x[0-9A-Fa-f]+|\d+)\s*\}', body):
            if m.group(1):
                xrefs.append((NUM(m.group(1)), m.group(2)))
            elif m.group(3) is not None:
                toks = [v.strip() for v in m.group(3).split(',') if v.strip()]
                if not all(re.fullmatch(r'0x[0-9A-Fa-f]+|\d+', t) for t in toks):
                    continue  # a database slip (an xref name where a byte belongs)
                vals = [NUM(t) for t in toks]
                for k, v in enumerate(vals[1:]):
                    pairs.append((vals[0] + k, v))
            else:
                pairs.append((NUM(m.group(4)), NUM(m.group(5))))
        if pairs or xrefs:
            pats[(name, ver)] = (xrefs, pairs, detect)
    return pats


def parse_table(path):
    text = preprocess(open(path, encoding='utf-8', errors='replace').read())
    prefixes = dict(re.findall(r'#define REGISTER_OOVPAS_(\w+)\(Symbol, \.\.\.\)\s+REGISTER_OOVPAS(?:_[MC])?_PREFIX\((\w+)', text))
    entries = []
    for m in re.finditer(r'REGISTER_OOVPAS(?:_(\w+))?\(\s*SYM_(FUN|VAR|FUN_ALT|FUN_LTCG)\(\s*(\w+)(?:\s*,\s*(\w+))?[^;]*?SYM_SIG\(([\d,\s]*)\)', text, re.S):
        macro, kind, name, alt, sigs = m.groups()
        prefix = prefixes.get(macro) if macro and macro not in ('M', 'C') else None
        if macro and macro.endswith(('_M', '_C')):
            prefix = prefixes.get(macro[:-2])
        sym = name + (alt if kind == 'FUN_ALT' and alt else '')
        xref = 'XREF_' + (prefix + '_' if prefix else '') + sym
        versions = [int(v) for v in sigs.split(',') if v.strip()]
        entries.append((sym, xref, versions))
    return entries


def load_xbe(path):
    d = open(path, 'rb').read()
    base = struct.unpack_from('<I', d, 0x104)[0]
    nsec, sec = struct.unpack_from('<II', d, 0x11C)
    sections = {}
    for i in range(nsec):
        fl, va, vsz, raw, rsz, nm = struct.unpack_from('<IIIIII', d, sec - base + i * 56)
        name = d[nm - base:d.index(b'\0', nm - base)].decode('latin-1')
        sections[name] = (va, d[raw:raw + rsz])
    return sections


def compile_pattern(pairs, xrefs):
    """A bytes regex for the pairs (xref offsets wildcarded); also the byte length it spans."""
    if not pairs:
        return None, 0
    span = max([o for o, _ in pairs] + [o + 4 for o, _ in xrefs]) + 1
    want = {}
    for o, v in pairs:
        want[o] = v
    rx = b''.join(re.escape(bytes([want[i]])) if i in want else b'.' for i in range(span))
    # a lookahead, so every offset is a candidate as in the library's byte scan: a match that
    # fails its xref check must not hide one starting inside it
    return re.compile(b'(?=' + rx + b')', re.S), span


def seed(text):
    k, sep, v = text.partition('=')
    if not sep or not k.startswith('XREF_'):
        raise argparse.ArgumentTypeError(f'{text!r} is not XREF_NAME=0xADDR')
    try:
        return k, int(v, 0)
    except ValueError:
        raise argparse.ArgumentTypeError(f'{v!r} is not an address') from None


def main():
    ap = argparse.ArgumentParser(description='Scan an XBE with XbSymbolDatabase\'s OOVPA patterns.')
    ap.add_argument('root', help='XbSymbolDatabase checkout, outside this repo')
    ap.add_argument('xbe')
    ap.add_argument('build', type=int, help='XDK build, for example 4361')
    ap.add_argument('--seed', type=seed, action='append', default=[], metavar='XREF_NAME=0xADDR')
    ap.add_argument('--seed-file', action='append', default=[], metavar='PATH',
                    help='name<TAB>0xADDR lines, each name tried as XREF_<name> and XREF_D3D_<name>')
    args = ap.parse_args()
    root, xbe_path, build = args.root, args.xbe, args.build
    db = os.path.join(root, 'src', 'OOVPADatabase')
    sections = load_xbe(xbe_path)
    lib_src = open(os.path.join(root, 'src', 'lib', 'libXbSymbolDatabase.c'), encoding='utf-8').read()
    xref = {}
    for name in re.findall(r'xref_database\[(XREF_\w+)\]\s*=\s*XREF_ADDR_DERIVE', lib_src):
        xref[name] = DERIVE
    for path in args.seed_file:
        for line in open(path):
            n, a = line.split('\t')[:2]
            for k in ('XREF_' + n, 'XREF_D3D_' + n):
                xref[k] = int(a, 0)
    for k, v in args.seed:
        xref[k] = v

    work = []  # (lib, sym, own xref, [(ver, pattern)])
    for lib, table, secs, folder in LIBS:
        pats = {}
        for f in sorted(os.listdir(os.path.join(db, folder))):
            pats.update(parse_inl(os.path.join(db, folder, f)))
        for sym, own, versions in parse_table(os.path.join(db, table)):
            revs = [(v, pats[(sym, v)]) for v in sorted(versions) if (sym, v) in pats]
            if revs:
                work.append((lib, sym, own, revs, secs))

    compiled = {}
    found = {}
    changed = True
    passes = 0
    while changed:
        changed = False
        passes += 1
        for lib, sym, own, revs, secs in work:
            if own in xref and xref[own] >= 0:
                continue
            low = [r for r in revs if r[0] <= build]
            high = [r for r in revs if r[0] > build]
            for group in (low, high):
                best = None
                for ver, (xrefs, pairs, detect) in group:
                    if any(xref.get(x, UNDET) == UNDET for _, x in xrefs):
                        continue
                    key = (sym, ver)
                    if key not in compiled:
                        compiled[key] = compile_pattern(pairs, xrefs)
                    rx, span = compiled[key]
                    if rx is None:
                        continue
                    hits = []
                    for sname in secs:
                        if sname not in sections:
                            continue
                        va, data = sections[sname]
                        for m in rx.finditer(data):
                            cur = m.start()
                            ok = True
                            for off, x in xrefs:
                                want = xref.get(x, UNDET)
                                if want == DERIVE:
                                    continue
                                if cur + off + 4 > len(data):
                                    ok = False
                                    break
                                got = struct.unpack_from('<I', data, cur + off)[0]
                                if got != want and (got + va + cur + off + 4) & 0xFFFFFFFF != want:
                                    ok = False
                                    break
                            if ok:
                                hits.append((va + cur, data, cur))
                    if not hits:
                        continue
                    pick = hits[detect - 1] if detect and len(hits) >= detect else hits[0]
                    best = (ver, pick, len(hits), xrefs)
                if best:
                    ver, (addr, data, cur), nhits, xrefs = best
                    for off, x in xrefs:
                        if xref.get(x) == DERIVE:
                            xref[x] = struct.unpack_from('<I', data, cur + off)[0]
                            found[x] = (xref[x], ver, 1, lib, 'derived from ' + sym)
                    xref[own] = addr
                    found[sym] = (addr, ver, nhits, lib, '' if group is low else 'revision above build')
                    changed = True
                    break
    for name, (addr, ver, n, lib, note) in sorted(found.items(), key=lambda kv: kv[1][0]):
        print(f'{name}\t0x{addr:X}\t{ver}\t{n}\t{lib}\t{note}')
    print(f'# {len(found)} found in {passes} passes', file=sys.stderr)


if __name__ == '__main__':
    main()
