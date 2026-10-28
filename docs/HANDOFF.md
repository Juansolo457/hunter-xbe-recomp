# Handoff: Hunter: The Reckoning (original Xbox) (2026-10-27)

State file. The next model starts here, not from chat history. Update it at the end of every
session. Goals and milestones: [PLAN.md](PLAN.md). Disc and XBE facts: [FINDINGS.md](FINDINGS.md).

## The ask (the user, 2026-10-27)
Static recompilation of **Hunter: The Reckoning** (Xbox, USA) in the shape of
https://github.com/TGP482/007FRWL-XBERecomp, built on TGP482's **XboxXBE-Recomp** SDK, which is
the standard to hit. **Linux first (Steam Deck first), with Vulkan.** Windows/PC later; D3D12
for PC maybe later. Follow the SDK's `templates/game` layout. Pull requests reviewed by
CodeRabbit (the user hooks the GitHub app up). Same house rules as the sibling recomps
(`../quake4-360-recomp/AGENTS.md`, `CONTRIBUTING.md`): master protected, PR + `audit` check +
up to date + threads resolved, admins too; source-only releases; never commit game data;
commit as `juansolo457 <5344231+Juansolo457@users.noreply.github.com>`; builds and game
windows need the user's OK first.

## Where it stands
**M0 started: the repository exists; nothing has been built.**
- GitHub: https://github.com/Juansolo457/hunter-xbox-recomp (public). `master` holds only the
  repo basics and the audit (first commit), and is locked (below). Everything else came in
  through the `bootstrap` pull request, which waits for CodeRabbit and the user.
- `sdk/`: XboxXBE-Recomp at `91146ff` (2026-10-27, 0.1.0, MIT), vendored, pinned in `sdk.toml`,
  without its `.github`. No changes to it yet.
- Template files from the SDK's `templates/game`, renamed for Hunter (`Hunter.exe`,
  `Hunter.dll`, `project(hunter)`). Issue templates from the 007 port.
- `config/game.toml`: placeholder with Hunter's `[xbe]` header (title, entry, xdk 4361, code
  sections). `src/common/game_info.cpp` filled in. `src/game/hooks.cpp` defines `DbgPrint`
  (ordinal 8), the one kernel import the SDK lacks.
- `build.sh` checks the XBE and stops at the first stage that doesn't exist yet.
- Tools tested on the real disc: `xiso.py` (list / extract all or some), `xbeinfo.py`,
  `xbeimports.py` (123 imports, 0 missing with hooks.cpp). `audit_repo.py` adapted to this repo
  (XBEH and RIFF magic, `assets/`, `generated/`, the `X86_FUNC(__imp__sub_...)` pattern
  xbe_recomp writes); `test_audit_repo.py` 6 cases pass.
- `.coderabbit.yaml`: assertive profile, path instructions for `sdk/`, `src/`, `config/`,
  `tools/`, `docs/`; `generated/`, `assets/`, `private/`, `out/` filtered out. CodeRabbit only
  reviews once the user installs the GitHub app on this repository.

## Next steps (M0, PLAN.md)
1. **XDK 4361 support**, with no build needed for the first part:
   - Make Hunter's `config/game.toml` by hand: for each name in
     `sdk/xdk/4831/signatures.toml` `[symbols]` and `[data]`, find it in Hunter (Ghidra or REA on
     `E:\OG-xbox-recomps\hunter-xbe\default.xbe`; library code lives in the `D3D`, `DSOUND`,
     `XGRPH`, `D3DX`, `XPP` sections, XAPI and CRT in `.text`), or leave it at 0 when the game
     doesn't link it. Comment each address with how it was proven. TGP482's 007 config is the
     model for a complete one.
   - `sdk/xdk/4361/layout.toml`: the 52 keys of the 4831 file, each proven at an address in
     Hunter's code (same method, same comments).
   - Then `xbe_symbols --sign config/game.toml --out sdk/xdk/4361/signatures.toml`
     (needs the tool built: step 2).
2. **The SDK tools on Linux** (needs the user's OK to build): `xbe_symbols` and `xbe_recomp`
   in WSL2. `cmake/XbeRecomp.cmake` is Windows-only (lld-link, .def files, WIN32 exe); split it
   so the tools and the code DLL/shared object build on Linux. Upstreamable.
3. First recompile, then the recompiled code compiling under clang on Linux.

## Facts found
In [FINDINGS.md](FINDINGS.md). Local paths not recorded there:
- The disc image: `E:\OG-xbox-recomps\Hunter - The Reckoning (USA).xiso.iso`, and the
  extracted `E:\OG-xbox-recomps\hunter-xbe\default.xbe`. Read-only; never commit them.
- SDK portability: the runtime (kernel, xdk, cpu, gpu shader/vertex/texture code) already
  compiles on Linux through `sdk/harness` (headless, no GPU). Windows-only: `runtime/app/*`,
  `gpu/d3d12.cpp`, `audio/xaudio2.cpp`, the ImGui win32/dx12 backends; `core/input.cpp` is SDL3.
  The recompiler and `xbe_symbols` sources have no Windows dependencies. Shaders are generated
  as HLSL (`gpu/shaders.cpp`); a Vulkan backend implements `gpu::Backend` (`gpu/backend.h`) and
  compiles that HLSL to SPIR-V. `gpu/ext.h` is D3D12-typed (unused by Hunter so far).
- Toolchains on this PC: VS 2022 Clang + CMake (`build.bat` finds them); WSL2 Ubuntu with
  clang 21.1.8, cmake 4.2.3, ninja, glslc, Vulkan headers, 16 threads.

## Steam Deck
The user (2026-10-27): do not set up or test the Deck SSH path until a first build is ready to be
played. Until then everything runs on this PC (WSL2 for Linux builds). Deck details are in memory
`steam-deck-ssh` when that time comes.

## Master lock (day 1, non-negotiable)
Right after the first push: `gh api -X PUT repos/Juansolo457/hunter-xbox-recomp/branches/master/protection`
with `required_status_checks: {strict: true, contexts: ["audit"]}`, `enforce_admins: true`,
`required_pull_request_reviews: {required_approving_review_count: 0}`,
`required_conversation_resolution: true`, `allow_force_pushes: false`, `allow_deletions: false`,
`restrictions: null`. Every later change, the bootstrap included, goes in through a pull request.

## Decisions taken as defaults (the user may change them)
1. Repo name `hunter-xbox-recomp` (sibling naming), public like the other recomps.
2. The SDK vendored as a copy in `sdk/`, changes offered upstream with `sdk/tools/sdk_sync`; no
   fork yet.
3. No build until the user OKs one (step 2 above is the first).
