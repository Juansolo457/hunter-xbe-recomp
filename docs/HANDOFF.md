# Handoff: Hunter: The Reckoning (original Xbox) (2026-10-28)

State file. The next model starts here, not from chat history. Update it at the end of every
session. Goals, decisions and milestones: [PLAN.md](PLAN.md). Disc and XBE facts:
[FINDINGS.md](FINDINGS.md).

## The ask (the user)
Static recompilation of **Hunter: The Reckoning** (Xbox, USA) in the shape of
https://github.com/TGP482/007FRWL-XBERecomp, on TGP482's **XboxXBE-Recomp** SDK, the standard to
hit. Order, as with GRAW: **Windows D3D12 first** with the SDK as it ships, then the **Steam
Deck through Proton**, then **native Linux with Vulkan**. Pull requests reviewed by CodeRabbit
(the user installs the GitHub app). House rules as in the sibling recomps: master protected,
source-only releases, never commit game data, commit as
`juansolo457 <5344231+Juansolo457@users.noreply.github.com>`. Builds and test windows are free in
this repo; never close a game the user is running.

The first session (2026-10-27) started Linux-first; the user corrected the order on 2026-10-28
after an internet outage mixed up two sessions. The docs now follow the corrected order.

## Where it stands
**M0 started: the repository is up; nothing has been built.**
- https://github.com/Juansolo457/hunter-xbe-recomp (public). `master` holds the repo basics
  and the audit and is locked (below). Everything else comes in through the `bootstrap` pull
  request, which waits for CodeRabbit and the user.
- `sdk/`: XboxXBE-Recomp at `91146ff` (2026-10-27, 0.1.0, MIT), unchanged, pinned in
  `sdk.toml`, without its `.github`.
- Template files from the SDK's `templates/game`, renamed for Hunter (`Hunter.exe`,
  `Hunter.dll`, `project(hunter)`). Issue templates from the 007 port.
- `config/game.toml`: placeholder with Hunter's `[xbe]` header (title, entry, xdk 4361, code
  sections). `config/xdk/4361/` holds only a README so far. `src/common/game_info.cpp` filled
  in. `src/game/hooks.cpp` has no hooks: the SDK implements all 123 kernel imports, `DbgPrint`
  (ordinal 8) included.
- Tools tested on the real disc: `xiso.py` (list, extract all or some), `xbeinfo.py`,
  `xbeimports.py` (123 imports, 0 missing). `audit_repo.py` adapted to this repo;
  `test_audit_repo.py`, 6 cases, pass.
- `build.sh` is a stub until M5.

## Next steps (M0)
1. **Make Hunter's `config/game.toml` by hand.** For each name in
   `sdk/xdk/4831/signatures.toml` `[symbols]` and `[data]`, find it in Hunter (Ghidra or REA on
   `E:\OG-xbox-recomps\hunter-xbe\default.xbe`; library code lives in the `D3D`, `DSOUND`,
   `XGRPH`, `D3DX`, `XPP` sections, XAPI and the CRT in `.text`), or leave it at 0 when the game
   doesn't link it. Comment each address with how it was proven. TGP482's 007 config is the
   model for a complete one.
2. **`config/xdk/4361/layout.toml`**: the 52 keys of the 4831 file, each proven at an address in
   Hunter's code, with the same comment style.
3. **Wire the overlay in.** `build.bat` passes `%SDK%\xdk` to `xbe_symbols`, and
   `add_xbe_image` in `sdk/cmake/XbeRecomp.cmake` passes `${XBE_SDK_DIR}/xdk` to `xbe_recomp`.
   Point both at a folder holding the SDK's builds plus `config/xdk/4361`, from this repo's
   `CMakeLists.txt` and `build.bat`, with `sdk/` unchanged (for example, copy both into
   `out/build/release/xdk` at configure time). Then sign:
   `xbe_symbols --sign config/game.toml --out config/xdk/4361/signatures.toml`.
4. **First build** with `build.bat` (VS 2022 Clang + CMake are installed): recompile, compile,
   link `Hunter.exe`.

## Local paths (not in FINDINGS.md)
- The disc image: `E:\OG-xbox-recomps\Hunter - The Reckoning (USA).xiso.iso`; the extracted
  `E:\OG-xbox-recomps\hunter-xbe\default.xbe`. Read-only; never commit them. Extract into
  `assets/` with `python -I tools/xiso.py <iso> extract assets` before the first build.
- For M5 later: the SDK runtime's kernel, XDK and gpu shader code already compile on Linux
  through `sdk/harness` (headless). Windows-only are `runtime/app/*`, `gpu/d3d12.cpp`,
  `audio/xaudio2.cpp` and the ImGui win32/dx12 backends; `cmake/XbeRecomp.cmake` uses lld-link
  and .def files.

## Steam Deck
Do not set up or test the Deck SSH path until a first build is ready to be played. Deck details
are in memory `steam-deck-ssh` when that time comes; the Deck runs the Windows build in Proton.

## Master lock (day 1, non-negotiable)
Applied right after the first push: `required_status_checks: {strict: true, contexts:
["audit"]}`, `enforce_admins: true`, `required_pull_request_reviews:
{required_approving_review_count: 0}`, `required_conversation_resolution: true`,
`allow_force_pushes: false`, `allow_deletions: false`, `restrictions: null`. Every later change,
the bootstrap included, goes in through a pull request.
