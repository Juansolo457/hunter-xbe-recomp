# Plan: Hunter: The Reckoning (original Xbox), statically recompiled

Written 2026-10-27 from the user's brief. State and next steps: [HANDOFF.md](HANDOFF.md); disc and
XBE facts: [FINDINGS.md](FINDINGS.md).

## Goal
The Xbox Hunter: The Reckoning running natively, its x86 code translated to C++ with TGP482's
[XboxXBE-Recomp](https://github.com/TGP482/XboxXBE-Recomp) SDK, to the standard of
[007FRWL-XBERecomp](https://github.com/TGP482/007FRWL-XBERecomp): resolution, frame rate,
anti-aliasing, field of view, mouse and keyboard, rebinding, gyro, texture replacement.

Platforms, in order:
1. **Linux, the Steam Deck first**, drawn with **Vulkan**. The first bar: the whole game at a
   locked frame rate on the Deck.
2. **Windows / PC**, with the same Vulkan renderer.
3. **Direct3D 12 on PC, maybe later**: the SDK's own renderer, if it earns its keep.

## Decisions (the user, 2026-10-27)
- **The SDK and the 007 port are the template**: the SDK's `templates/game` layout, `sdk/` in
  the repo, `config/game.toml`, `src/common` and `src/game`.
- **Linux first, Vulkan.** The SDK draws with Direct3D 12 and runs only on Windows today (its
  headless harness aside). The Linux layers are added to `sdk/` and offered upstream.
- **CodeRabbit reviews every pull request**; `master` is protected like the sibling recomps.
- **Source only.** No release ships the game's code; players build from their own disc.

Defaults taken without the user (change by asking): repository name `hunter-xbox-recomp`, the
SDK vendored as a copy (`sdk.toml` pin) rather than a fork or submodule, game code linked at
build time on Linux (the SDK's first-launch compile stays a Windows feature for now).

## Architecture
```
assets/default.xbe --xbe_symbols--> config/game.toml (XDK functions and data the host replaces)
                   --xbe_recomp----> generated/game (C++, one function per guest function)
                                          |
src/          game info, options, hooks over recompiled functions (X86_FUNC)
sdk/runtime   kernel, XDK HLE (D3D8, DirectSound, XAPI), cpu dispatch, gpu state and shaders
  Windows:    app (Win32), gpu/d3d12.cpp, audio/xaudio2.cpp  (as shipped)
  Linux:      app over SDL3, gpu/vulkan.cpp, audio over SDL3  (this project)
```
The SDK's renderer translates the Xbox's vertex programs, combiners and fixed function state to
HLSL (`gpu/shaders.cpp`). The Vulkan backend compiles that HLSL to SPIR-V (DXC as a library, a
pipeline cache on disk), so one shader translator serves both APIs.

## Milestones
| # | Milestone | Done when |
|---|---|---|
| M0 | **Repo and XDK 4361** | Repo public and protected; `config/game.toml` complete for Hunter (every symbol `xbe_symbols` reads for 4831 found in Hunter, or proven absent); `sdk/xdk/4361/layout.toml` with each key proven in Hunter's code; `sdk/xdk/4361/signatures.toml` signed from it; `xbe_symbols` and `xbe_recomp` build and run on Linux; the recompiled code compiles |
| M1 | **Headless boot on Linux** | `sdk/harness` runs Hunter in WSL/Linux: kernel and XDK calls hold, the title reaches its front end menu, reference-renderer captures show it |
| M2 | **Vulkan and the Linux app** | SDL3 window and pads, SDL3 audio, `gpu::Backend` on Vulkan; menus and the first level drawn correctly on desktop Linux |
| M3 | **Steam Deck** | A Deck build in `~/recomps/Hunter-SteamDeck/`; the user plays it through, locked frame rate, logs collected |
| M4 | **007 parity options** | Display, graphics, input and general options the 007 port has, that make sense for Hunter |
| M5 | **Windows** | The same Vulkan path on Windows; the D3D12 question decided |

## Risks
- **XDK 4361 is older than anything the SDK supports.** D3D8 structure offsets, render state
  numbering and DirectSound internals may differ from 4831. Every layout key gets proven in
  Hunter's code, not assumed.
- **Libraries the SDK hasn't met:** DirectMusic (linked, use unproven), the WMA decoder and the
  Dolby encoder sections, Bink inside `.text`. Each needs HLE or must be proven harmless.
- **The SDK is young (0.1.0) and Windows-shaped.** Linux changes touch many files; keep them
  small and upstreamable so syncing stays possible.
