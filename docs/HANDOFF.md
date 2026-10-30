# Handoff: Hunter: The Reckoning (original Xbox) (2026-10-28, boots to the menu)

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
`juansolo457 <5344231+Juansolo457@users.noreply.github.com>`. Ask the user before any build or
test run (since 2026-10-29); never close a game the user is running.

The first session (2026-10-27) started Linux-first; the user corrected the order on 2026-10-28
after an internet outage mixed up two sessions. The docs follow the corrected order.

## Where it stands
**M1 in progress: the game boots on Windows and plays: menus, a new game, moving around, characters
rendered correctly, smooth (user, 2026-10-28). Weapon and enemy sounds were silent (DirectMusic's
clock, step 12): fixed and confirmed by the user 2026-10-29. No known bugs in what has been played.**
- GitHub: https://github.com/Juansolo457/hunter-xbe-recomp (public), master locked (below).
  Everything so far came in through three stacked PRs, merged in order at the user's request:
  #1 `bootstrap` and #2 `m0-first-build` (the first build) on 2026-10-29 local time (2026-10-30
  UTC on GitHub), then #3 `m1-boot`, this boot work, which carries this file. CodeRabbit reviews
  every PR into master; each one's threads are fixed or answered before it merges.
- `config/game.toml`: 156 of 268 XDK functions and 11 of 13 data addresses, each labelled with where it
  came from (`tools/make_config.py` writes it; FINDINGS.md). 112 names are at 0: 37 are
  networking names Hunter doesn't link, the rest not found or not called yet.
- `config/xdk/4361/layout.toml`: 44 keys, each proven at an address in Hunter's code, including
  the render state numbering (below).
- A test run: `out/build/release/Hunter.exe`, windowed 1280x720 through
  `out/build/release/settings.toml`. A 60 s run is clean (no errors in the log).

## What made it boot (2026-10-28)
Each stop, its cause and the fix, in order:
1. D3D tables unknown: `D3D_RenderState 0x20FE30`, `D3D_SimpleRenderStateEncode 0x2656D0`,
   `D3D_DeferredTextureState 0x20FC30`, read from 4361's `SetRenderStateNotInline` (`0x200C00`)
   and `SetTextureStageStateNotInline` (`0x201510`), both now in the config.
2. **4361 numbers render states differently** (146 states; deferred from 82, complex from 117,
   no SampleAlpha): the runtime indexed the title's table with 4831's numbers. SDK change:
   `GuestRs`/`HostRs` in `sdk/runtime/xdk/d3d8.cpp`, driven by three new optional layout keys
   (`RenderState_Deferred`, `RenderState_Complex`, `RenderState_Dxt1NoiseEnable`; 4831 defaults).
3. Divide by zero in the game: `Get2DSurfaceDesc` reports the device's multisample type for the
   back buffer, which the runtime never set. SDK change: new optional key
   `CDevice_MultiSampleType`, set to D3DMULTISAMPLE_NONE with the frame buffers.
4. DirectSound methods running console code on host objects, one crash each:
   `IDirectSound_SetMixBinHeadroom`, `IDirectSoundBuffer_AddRef`, `IDirectSound_SetAllParameters`,
   `CDirectSoundStream_SetOutputBuffer`, `IDirectSoundBuffer_SetPitch`/`CDirectSoundStream_SetPitch`.
   SDK changes: the last five added to `sdk/runtime/xdk/dsound.cpp`. The SDK's signature match
   for `IDirectSoundBuffer_SetRolloffCurve` was wrong (that wrapper is SetConeAngles): now 0.
5. Effects image keys (`EffectsImage_*`, same as 4831) proven and added.
6. **A recompiler bug**: `push ds`/`push es` moved esp by 2, their pops by 4, so Bink's CPU check
   (`0x1E6CC0`) unbalanced its caller's stack and the first movie crashed. SDK change in
   `sdk/tools/recomp/codegen_int.cpp`: a segment register push takes a 4 byte slot.
7. No vertical blank: the runtime only starts its vblank thread with `CDevice_VBlankCount`
   (`0x2460`), `CDevice_VBlankCallback` (`0x2430`) and the event; proven in the vblank DPC handler
   `0x20A970` and added.
8. `D3DDevice_Reset` (`0x202C70`) ran the library's own frame buffer setup; mapped to the runtime's.
9. **Black frames**: `D3D_InitDefaultState` (`0x208D30`) was not mapped, so no default render
   states (colour write mask 0, depth function NEVER). Mapped: the movies and the menu show.
10. Crash picking a game mode in the menu: the DSOUND library's own synth (`0x21F9xx`, likely
    DirectMusic's) calls buffer and stream methods the runtime lacked. A scan of every caller of
    the buffer and stream methods found twelve: buffer SetLFO, SetNotificationPositions,
    SetConeAngles, SetConeOrientation, SetConeOutsideVolume, SetMode; stream SetLFO, SetEG,
    SetAllParameters and the three cone setters. All added to the runtime (LFOs and cones as
    no-ops, as the envelope and filter already are; SetMode and stream SetAllParameters keep the
    3D state). SetNotificationPositions' events were not signalled yet at this step; step 12
    added that. With this the user got past the game mode to the character select.
11. **Torn characters** (limbs, eyes, silhouettes in the wrong place; the user's screenshot, 2026-10-28):
    Hunter skins characters with the fixed function pipeline: FVF `0x116` (one blend weight), the
    engine's skinning setup `0x15F3E0` maps 2 3 4 bones to D3DRS_VERTEXBLEND 1 3 5 (table `0x2769AC`)
    and sets each bone with `SetTransform(6 + i)` through its matrix cache `0x1609D0`. Two SDK gaps:
    the fixed function vertex shader ignored VERTEXBLEND, and the render thread copied world matrix 0
    only (an in-game F3 capture showed w1 all zeros). Both fixed in the SDK (vertex blending in
    `gpu/shaders.cpp` with world 1 to 3 constants filled in `gpu/d3d12.cpp`; the render thread copies
    the four world matrices). The user confirmed the characters are right.
12. **Silent effects** (weapon, enemy and other DirectMusic sounds; only ambience played): DirectMusic's
    reference clock (`0xEC8A5`) advances by `DirectSoundGetSampleTime`, which the library reads from the
    APU only for its own DirectSound object, so under the runtime it returned 0, the clock never moved,
    and DirectMusic never played anything. SDK fix: `DirectSoundGetSampleTime` returns the samples the
    mixer has rendered at 48 kHz. A 40 s smoke run then logged dozens of effect voices where the user's
    8 minute session had about 30 in all. On the way: SetNotificationPositions now signals its events as
    the play cursor passes their offsets (and DSBPN_OFFSETSTOP ones on stop); IDirectSoundStream create,
    SetMode, SetMaxDistance, SetMinDistance, SetMixBinVolumes added. **The user confirmed the sound is
    fixed (2026-10-29).**

## SDK changes to offer upstream (TGP482/XboxXBE-Recomp)
`sdk/` was unchanged until this work; every change here is portable and game-agnostic:
- `tools/recomp/codegen_int.cpp`: 4 byte segment register pushes (a real recompiler bug).
- `runtime/xdk/d3d8.cpp`, `runtime/xdk/layout.h`: render state numbering for XDKs before 4627;
  `CDevice_MultiSampleType`.
- `runtime/xdk/dsound.cpp`: `IDirectSoundBuffer_AddRef`, `IDirectSoundBuffer_SetPitch`,
  `CDirectSoundStream_SetPitch`, `CDirectSoundStream_SetOutputBuffer`, `IDirectSound_SetAllParameters`,
  and the twelve buffer and stream methods of step 10; `IDirectSound_CreateSoundStream`, stream SetMode;
  `DirectSoundGetSampleTime` from the mixer's sample count; SetNotificationPositions events; the
  `XBE_AUDIO_LOG` diagnostic.
- `runtime/gpu/shaders.cpp`, `shaders.h`, `d3d12.cpp`, `render_thread.cpp`: fixed function vertex blending
  (D3DRS_VERTEXBLEND 1 to 6) and the four world matrices reaching the render thread; the F3 capture
  lists each draw's blend mode and world translations.
- The 4361 overlay itself (`config/xdk/4361/layout.toml`, signatures still to sign).

Unchanged here, to report (from CodeRabbit's reviews):
- The recompiler models no segment registers: reads give 0, writes are dropped, FS addressing goes
  through `fs_base`. So `push ds` pushes 0, not the console's selector. Step 6 fixed only the slot
  size; the one code met (Bink's CPU check) pushes and pops in pairs and never reads the slots.
- `tools/sdk_sync/sdk_sync.py` reads `overrides` from the top level of a game's `sdk.toml`, but
  `set_pin` writes it under `[sdk]`, where it is ignored; `set_pin` also updates only `version`,
  never `commit`. This repo keeps `overrides` at the top level and updates `commit` by hand.
- `THIRD_PARTY.txt` lacks the Zydis notice, though `xbe_recomp` links Zydis.

## Next steps (M1)
1. **Play further**: saves, later levels and co-op are untested. Expect more DirectSound and D3D
   names the game calls but the config lacks: `tools/` has no automatic list yet, see the method in
   "Debugging" below. `D3DDevice_SetVertexShaderConstant` (`0x205470`) runs as console code (the
   SDK only knows the later variants); check whether constants reach the renderer.
2. Gamma: 4361 keeps one pending gamma index (`+0x2A8C`), the runtime expects a flag per ramp;
   gamma changes are not applied yet.
3. DirectMusic now plays (step 12); the WMA decoder and Dolby sections: not met yet.

## Debugging
- Release builds log only errors and Report lines (`NDEBUG`); `out/build/debug` (preset `debug`,
  -O3, every log line) is configured and built for verbose runs.
- A crash: `python -I tools/crashsite.py out/build/release/CrashDumps/<dump> out/build/release/Hunter.dll`
  names the guest function; the log's guest stack gives the callers. Direct calls between
  recompiled functions skip `[xbe] trace` wrappers, so a trace only catches indirect calls.
- F3 in the game window dumps every guest thread's stack; with `XBE_CAPTURE_DIR` set it also saves
  the next frame (draws, targets, shaders). The window takes `PostMessage` keys without focus.
- Entry points the game calls that the runtime doesn't replace: scan `.text` for `call`/`jmp`
  into the D3D or DSOUND section and compare with the config (this session's script did that
  by hand; worth turning into `tools/`).

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
- `CMakeLists.txt` copies `config/xdk/` into the compiler folder (the first-launch compile reads
  it) and refreshes `Hunter.dll`'s time after the exe links, so a host-only change doesn't make the
  exe rebuild its code at start. That holds for `build.bat`'s DLL, which has no stamp. Once a
  first-launch build has written `built.txt` in the compiler's work folder, the stamp (the exe's
  size and time and the xbe's SHA-1) decides instead (`sdk/runtime/app/game_code.cpp`, `Current`),
  so any relink of the exe rebuilds the code at the next start.

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
