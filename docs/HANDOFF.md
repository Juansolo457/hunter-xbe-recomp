# Handoff: Hunter: The Reckoning (original Xbox) (2026-10-28)

State file. The next model starts here, not from chat history. Update it at the end of every
session. Goals, decisions and milestones: [PLAN.md](PLAN.md). Disc and XBE facts:
[FINDINGS.md](FINDINGS.md).

## The ask (the user)
Static recompilation of **Hunter: The Reckoning** (Xbox, USA) in the shape of
https://github.com/TGP482/007FRWL-XBERecomp, on TGP482's **XboxXBE-Recomp** SDK, the standard to
hit. Order, as with GRAW: **Windows D3D12 first** with the SDK as it ships, then the **Steam
Deck through Proton**, then **native Linux with Vulkan**. Pull requests reviewed by CodeRabbit
later (the user installs the GitHub app; not yet). House rules as in the sibling recomps:
master protected, source-only releases, never commit game data, commit as
`juansolo457 <5344231+Juansolo457@users.noreply.github.com>`. Builds and test windows are free in
this repo; never close a game the user is running.

The first session (2026-10-27) started Linux-first; the user corrected the order on 2026-10-28
after an internet outage mixed up two sessions. The docs follow the corrected order.

## Where it stands
**M0 built: `Hunter.exe` builds and links on Windows. M1 (boot) starts: the first run stops in
D3D setup at 0.19 s on three unknown data addresses.**
- GitHub: https://github.com/Juansolo457/hunter-xbe-recomp (public), master locked (below).
  PR #1 `bootstrap` (repo, SDK copy, template, tools, docs) and the `m0-first-build` PR on top
  of it are open. CodeRabbit is not installed yet: merge once the user has reviewed.
- `config/game.toml`: 129 of 248 XDK functions and 8 of 13 data addresses, each labelled with
  where it came from (FINDINGS.md, "The XDK functions and data the host replaces"). 118 are at
  0: 37 networking names Hunter doesn't link, the rest not found yet.
- `config/xdk/4361/layout.toml`: 34 keys, every one proven at an address in Hunter's code; all
  the keys the runtime requires are there. `config/game.toml` includes it with a top-level
  `includes = [...]` instead of `[xbe] xdk = 4361`, so `sdk/` stays unchanged.
- The build: `build.bat` (fixed to strip quotes from PATH, which broke VsDevCmd on this PC).
  The first recompile and compile took a few minutes on 14 jobs: 18,848 functions, 340 jump
  tables, 2.17 of 2.42 MB of code bytes. `generated/game` is 123 MB (ignored).
- First run (windowed 1280x720 through `out/build/release/settings.toml`): the game is found in
  `assets/` with the right SHA-1, the code DLL loads, then
  `d3d: D3D_DeferredTextureState / D3D_RenderState / D3D_SimpleRenderStateEncode is unknown`
  and the runtime aborts (exit `0xC0000409`, a dump in `out/build/release/CrashDumps`).

## Next steps (M1, boot)
1. **The three D3D tables.** `D3D_RenderState` is the base of the render state array: the
   `D3DDevice_SetRenderState_*` functions store to it (StencilEnable at `0x201A00` reads
   `0x210024`, `0x210064`, `0x210068`). `D3D_DeferredTextureState`: the oovpa scan derived
   `XREF_D3DTSS_TEXCOORDINDEX = 0x20FCA0` (SetTextureState_TexCoordIndex `0x201317` stores
   `[stage * 128 + 0x20FCA0]`); the base is that minus TexCoordIndex's index * 4.
   `D3D_SimpleRenderStateEncode` is the method table `D3DDevice_SetRenderState_Simple`
   (`0x200BD0`) reads. XbSymbolDatabase's `manual_d3d8__ltcg.h` and its render state table
   (`DxbxRenderStateInfo`, with the 4361 ranges) show how they are found.
2. **Check the render state numbering.** `sdk/runtime/gpu/state.h` hard-codes the D3DRS indices
   of 4831/5849. If 4361 numbers them differently (the XbSymbolDatabase table says which), the
   runtime needs a 4361 mapping: that would be the first SDK change, made upstream-ready.
3. Then run again and fix each stop: missing functions (the non-network ones the game calls),
   DirectMusic, the WMA and Dolby sections, Bink in `.text`.

## How it is built and run
```
python -I tools/xiso.py "E:\OG-xbox-recomps\Hunter - The Reckoning (USA).xiso.iso" extract assets
build.bat                                    # VS 2022 Clang, CMake, Ninja; CI=1 skips its prompts
out\build\release\Hunter.exe                 # finds assets/ in a folder above it
```
- `out/build/release/settings.toml` with `display_mode = "windowed"`, `width = 1280`,
  `height = 720` keeps test windows off the whole screen (modes are lowercase).
- After editing `config/xdk/4361/layout.toml`, touch `config/game.toml`: the recompile step
  depends on `config/*.toml` and the SDK's xdk files, not the overlay.
- Before a release: the first-launch compile on a player's PC copies `config/*.toml` into the
  compiler folder (`compiler_files` in `sdk/cmake/XbeRecomp.cmake`) but not `config/xdk/`, so the
  overlay must reach it too (or land upstream first).

## Tools
| | |
|---|---|
| `tools/xiso.py <iso> list \| extract <dir> [paths]` | XDVDFS reader |
| `tools/xbeinfo.py <xbe>` | header, sections, XDK builds (entry key fixed: entry is `0xA27C1`) |
| `tools/xbeimports.py <xbe>` | kernel imports against the SDK and `src/` |
| `tools/oovpa_scan.py <XbSymbolDatabase checkout> <xbe> 4361 [--seed X=0x..] [--seed-file f]` | XbSymbolDatabase patterns matched as data; checkout outside the repo |
| `tools/xbedis.py <xbe> <addr or name> [n]` | capstone disassembly naming known addresses (capstone in a virtual environment, run with its interpreter and `-I`) |
| `out/build/release/xbe_symbols.exe` | the SDK's scanner; with the 4831 set copied as `<tmp>/4361` it gives the "sig"/"k=" finds |

## Local paths (not in FINDINGS.md)
- The disc image: `E:\OG-xbox-recomps\Hunter - The Reckoning (USA).xiso.iso`; the extracted
  `E:\OG-xbox-recomps\hunter-xbe\default.xbe`. Read-only; never commit them. `assets/` holds the
  extracted disc (ignored).
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
