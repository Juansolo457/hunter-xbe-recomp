"""Check what git would publish for game material: run before every push (CI runs it too).

    python -I tools/audit_repo.py                 every file in the index: tracked plus staged
    python -I tools/audit_repo.py --history       every file in every commit (a report: history
                                                  isn't rewritten by anything here)
    python -I tools/audit_repo.py --install-hook  run it from .git/hooks/pre-push too (optional)

It reads git's own blobs (git cat-file), never the working tree, so local junctions to game data
or the toolchain can't hide or add anything. It rejects:
  - folders that only ever hold game material or builds (private/, assets/, the recompiled code
    in generated/, build output, logs, saves, crash dumps, texture dumps);
  - game file types and executable or archive payloads, by extension and by the first bytes
    (XBEH, PE/MZ, ELF, ZIP, 7z, RAR, RIFF, DDS, Bink, Xbox packed resources);
  - recompiled game code (the X86_FUNC(__imp__sub_XXXXXXXX) definitions xbe_recomp writes; a
    hook in src/ defines X86_FUNC(sub_...) and only calls __imp__), symlinks, submodules and
    anything over 2 MB, except the reviewed exceptions below.

This catches the common accidents, not every copyright question: a clean run doesn't make a
change legally safe. Releases stay source only: never attach builds, game files or the private
test packages (private/) to a release. Adapted from the script in quake4-360-recomp,
graw360-recomp and fear360-recomp.
"""
import os
import re
import subprocess
import sys

# Folders that only hold game material, data derived from it, builds or local state.
PROHIBITED_PATHS = [
    (r'(^|/)private/', 'private/ (the disc, captures, test packages)'),
    (r'^assets/', 'assets/ (the game files)'),
    (r'^generated/', 'generated/ (the recompiled game code)'),
    (r'^(out|build)/', 'build output'),
    (r'^(logs|hdd|cap|crashdumps|textures)/', 'logs, saves, captures, crash dumps or texture dumps'),
    (r'^(\.tools|third_party)(/|$)', 'toolchain or a downloaded checkout'),
]
# Game files and binaries, by extension.
PROHIBITED_EXTENSIONS = {
    '.iso', '.xiso', '.xbe', '.xex', '.bik', '.xpr', '.xbx', '.wma', '.wav', '.jam',
    '.exe', '.dll', '.so', '.lib', '.a', '.obj', '.o', '.pdb', '.ilk', '.dmp',
    '.zip', '.7z', '.rar', '.bin',
}
# First bytes of executables, archives and game formats.
SIGNATURES = [
    (b'XBEH', 'Xbox executable (XBE)'),
    (b'XEX2', 'Xbox 360 executable (XEX2)'),
    (b'MZ', 'Windows executable (MZ/PE)'),
    (b'\x7fELF', 'ELF executable'),
    (b'PK\x03\x04', 'ZIP archive'),
    (b'7z\xbc\xaf\x27\x1c', '7z archive'),
    (b'Rar!', 'RAR archive'),
    (b'RIFF', 'RIFF audio or video'),
    (b'DDS ', 'DDS texture'),
    (b'BIK', 'Bink video'),
    (b'XPR0', 'Xbox packed resource'),
    (b'XPR1', 'Xbox packed resource'),
]
MAX_SIZE = 2 * 1024 * 1024
# What xbe_recomp writes for every guest function; in two parts, so this file doesn't match itself.
TRANSLATED_FUNCTION = re.compile(rb'X86_FUNC\(__imp_' + rb'_sub_[0-9A-Fa-f]{8}\)')

# Reviewed exceptions: (path regex, rule it is exempt from, why).
EXCEPTIONS = []


def git(*args, data=None):
    return subprocess.run(['git', *args], input=data, capture_output=True, check=True).stdout


def exempt(path, rule):
    return any(re.search(pattern, path) and kind in (rule, 'any') for pattern, kind, _ in EXCEPTIONS)


def index_blobs():
    """(mode, sha, path) of every file in the index: what the next commit would contain."""
    out = []
    for entry in git('ls-files', '-s', '-z').split(b'\0'):
        if entry:
            meta, path = entry.split(b'\t', 1)
            mode, sha, _stage = meta.split()
            out.append((mode.decode(), sha.decode(), path.decode('utf-8', 'replace')))
    return out


def history_blobs():
    """(mode, sha, path) of every file in every commit reachable from any ref, under each path
    it had. Each commit's whole tree is listed: `git rev-list --objects` names an object only
    once, so content stored under an allowed and a prohibited path would be checked under one of
    them only, and it gives no modes (symlinks and submodules)."""
    out = set()
    for commit in git('rev-list', '--all').decode().split():
        for entry in git('ls-tree', '-r', '-z', '--full-tree', commit).split(b'\0'):
            if not entry:
                continue
            meta, path = entry.split(b'\t', 1)
            mode, kind, sha = meta.split()
            if kind in (b'blob', b'commit'):  # a commit entry is a submodule
                out.add((mode.decode(), sha.decode(), path.decode('utf-8', 'replace')))
    return sorted(out, key=lambda blob: (blob[2], blob[1]))


def read_blobs(shas):
    """{sha: content} through one git cat-file --batch."""
    raw = git('cat-file', '--batch', data=''.join(f'{s}\n' for s in shas).encode())
    contents, pos = {}, 0
    while pos < len(raw):
        header_end = raw.index(b'\n', pos)
        sha, _kind, size = raw[pos:header_end].split()
        size = int(size)
        contents[sha.decode()] = raw[header_end + 1:header_end + 1 + size]
        pos = header_end + 1 + size + 1
    return contents


def problems(mode, path, data):
    found = []
    low = path.lower()
    # By mode, never exempted: an exemption names a path whose contents are fine, and a symlink
    # or submodule there would point somewhere else.
    if mode == '120000':
        found.append(('mode', 'symlink (could point at game data)'))
    if mode == '160000':
        found.append(('mode', 'submodule'))
    for pattern, why in PROHIBITED_PATHS:
        if re.search(pattern, low):
            found.append(('path', why))
    ext = os.path.splitext(low)[1]
    if ext in PROHIBITED_EXTENSIONS:
        found.append(('extension', f'{ext} file (game data, binary or archive)'))
    if data is None:
        return found
    for magic, why in SIGNATURES:
        if data.startswith(magic) and (magic != b'MZ' or b'\0' in data[:512]):
            found.append(('signature', why))
    if len(data) > MAX_SIZE:
        found.append(('size', f'{len(data) / 2**20:.1f} MB (over {MAX_SIZE // 2**20} MB)'))
    if TRANSLATED_FUNCTION.search(data):
        found.append(('content', 'recompiled game code'))
    return [(rule, why) for rule, why in found if rule == 'mode' or not exempt(path, rule)]


def install_hook():
    hook = os.path.join(git('rev-parse', '--git-path', 'hooks').decode().strip(), 'pre-push')
    if os.path.exists(hook):
        sys.exit(f'{hook} exists already; add "python -I tools/audit_repo.py || exit 1" to it.')
    with open(hook, 'w', newline='\n') as f:
        f.write('#!/bin/sh\n# tools/audit_repo.py: no game material in what is pushed.\n'
                'python -I tools/audit_repo.py || exit 1\n')
    os.chmod(hook, 0o755)
    print(f'wrote {hook}')


def main():
    os.chdir(git('rev-parse', '--show-toplevel').decode().strip())
    if '--install-hook' in sys.argv:
        install_hook()
        return 0
    history = '--history' in sys.argv
    blobs = history_blobs() if history else index_blobs()
    wanted = sorted({sha for mode, sha, _ in blobs if mode not in ('160000',)})
    contents = read_blobs(wanted) if wanted else {}
    failures = []
    for mode, sha, path in blobs:
        for _rule, why in problems(mode, path, contents.get(sha)):
            failures.append((path, sha, why))
    scope = 'every commit' if history else 'the index (tracked and staged files)'
    if not failures:
        print(f'audit_repo: {len(blobs)} files in {scope}: no game material found.')
        return 0
    print(f'audit_repo: {len(failures)} problem(s) in {scope}:')
    for path, sha, why in sorted(set(failures)):
        print(f'  {path}  [{sha[:10]}]  {why}')
    if history:
        print('These are in history. Removing them from the tree does not remove them from the '
              'commits; rewriting history is a separate decision.')
    else:
        print('Unstage or remove these before committing (git rm --cached keeps a local copy).')
    return 1


if __name__ == '__main__':
    sys.exit(main())
