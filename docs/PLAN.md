# Plan: Hunter: The Reckoning (original Xbox), statically recompiled

Written 2026-10-27/28 from the user's brief and plan review. State and next steps:
[HANDOFF.md](HANDOFF.md); disc and XBE facts: [FINDINGS.md](FINDINGS.md).

## Goal
The Xbox Hunter: The Reckoning running natively, its x86 code translated to C++ with TGP482's
[XboxXBE-Recomp](https://github.com/TGP482/XboxXBE-Recomp) SDK, to the standard of
[007FRWL-XBERecomp](https://github.com/TGP482/007FRWL-XBERecomp).

## Decisions (the user)
- **The 007 port and the SDK template are reused unchanged first.** The SDK's
  `templates/game` layout, `sdk/` in the repo, `config/game.toml`, `src/common`, `src/game`.
- **Order, as with GRAW:**
  1. **Windows, Direct3D 12**, the SDK as it ships.
  2. **Steam Deck through Proton**: the Windows build, built on the PC and pushed over SSH.
  3. **Native Linux with Vulkan** last.
- **XDK 4361 as an overlay** in this repo (`config/xdk/4361/`): layout and signatures made by
  hand for Hunter, offered upstream as a pull request once complete. No SDK fork before the
  Linux phase.
- **0.1 is the game playing through.** 007's mouse and keyboard, texture replacement, HDR and
  draw distance are 1.0 features.
- **CodeRabbit reviews every pull request**; `master` is locked like the other recomps.
- **Source only.** No release ships the game's code; players build from their own disc.
- **Builds and test windows are free in this repo** while debugging; never close the user's
  running game.

## Architecture
```
assets/default.xbe --xbe_symbols--> config/game.toml (XDK functions and data the host replaces)
                   --xbe_recomp----> generated/game (C++, one function per guest function)
                                          |
src/          game info, options, hooks over recompiled functions (X86_FUNC)
sdk/runtime   kernel, XDK HLE (D3D8, DirectSound, XAPI), D3D12 renderer, XAudio2, SDL3 pads
config/xdk/4361   the XDK layout and signatures the SDK lacks for this build
```

## Milestones
| # | Milestone | Done when |
|---|---|---|
| M0 | **XDK 4361 and the first build** | `config/xdk/4361/layout.toml` with every key proven in Hunter's code; `config/game.toml` complete (every symbol the 4831 set names found in Hunter or proven absent); signatures signed from it; the overlay wired into the build; `Hunter.exe` links |
| M1 | **Boot on Windows** | The title reaches its front end menu; kernel and XDK gaps (DirectMusic, WMA, Dolby sections, Bink) handled |
| M2 | **Playable on Windows (0.1)** | The game plays through: levels, saves, co-op on one PC |
| M3 | **Steam Deck through Proton** | A push-over-SSH helper; the user plays on the Deck; Deck issues fixed in the Windows build |
| M4 | **007 parity (1.0)** | Mouse and keyboard, texture replacement, HDR, draw distance and the other 007 options that suit Hunter |
| M5 | **Native Linux** | SDK fork; Vulkan backend behind `gpu::Backend` (raw Vulkan + VMA, HLSL to SPIR-V with DXC), SDL3 app and audio; native on the Deck |

## Risks
- **XDK 4361 is older than anything the SDK supports.** D3D8 structure offsets, render state
  numbering and DirectSound internals may differ from 4831. Every layout key gets proven in
  Hunter's code, not assumed.
- **Libraries the SDK hasn't met:** DirectMusic (linked, use unproven), the WMA decoder and the
  Dolby encoder sections, Bink inside `.text`. Each needs HLE or must be proven harmless.
- **The SDK is young (0.1.0).** Keep `sdk/` unchanged so upstream updates drop in.
