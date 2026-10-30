# Findings: the disc and the XBE

Facts about Hunter: The Reckoning (USA), with how each was found. Read with `tools/xiso.py`,
`tools/xbeinfo.py` and `tools/xbeimports.py` (all `python -I`, read-only on the game's files).

## The disc
- An XISO (XDVDFS from offset 0, no video partition), 3.79 GB, 1549 files. Root sector 264.
- `default.xbe` beside a `Media` folder: level and UI archives (`*.JAM`, `*S.JAM` per level, plus
  `Kernel.JAM`, `Menu.JAM`, `IntroUI.JAM`, `InGameUI.JAM`), cutscene audio under
  `Media/Cinemas/<scene>/` (large WAVs per character, voices per language) and Visual
  SourceSafe leftovers (`vssver.scc`).

## default.xbe
| | |
|---|---|
| Size | 2,899,968 bytes |
| SHA-1 | `39735b530002b4e2da4182042591ef6e68ee08a0` |
| Title | `Hunter: The Reckoning`, title id `56550007`, region 1 (North America), version 1 |
| Built | 2002-04-01 (image), certificate 2002-04-03 |
| Debug path | `C:\DEVELOP\HUNTER\Build\code\HunterXDecember___Xbox_Release\HunterXDecember.exe` |
| Base | `0x10000` |
| Entry | `0xA27C1` (retail XOR key; `xbe_symbols` agrees) |
| Kernel thunk | `0x25F800` (in `.rdata`), 123 imports |
| TLS directory | `0x26BD44` |

### XDK libraries: all build 4361
XAPILIB, D3D8, DSOUND, DMUSIC, XBOXKRNL, LIBCMT, D3DX8, XGRAPHC. The SDK has signatures and
layouts for 4831 and 5849 only (`sdk/xdk/`), and `xbe_symbols` picks the set by the D3D8 or
XAPILIB build, so it stops on this XBE. See PLAN.md, M0.

### The XDK functions and data the host replaces
`config/game.toml` was made in three passes (2026-10-28):
1. `xbe_symbols` with the 4831 signatures copied under a 4361 folder name: 70 of 248 functions,
   6 of 13 data. 15 of those matched by constants only; each is labelled with its score.
2. XbSymbolDatabase's OOVPA patterns (MIT code, ODbL database, not vendored) read as data by a
   Python matcher that mirrors the library's automatic scan; run outside the repo. It agrees with
   `xbe_symbols` on all 46 functions both found, and adds 60, 12 of which it found only once
   seeded with the device pointer and the step 1 results. (Since then the matcher also tests
   overlapping offsets, as the library does; that adds five `IDirectSoundStream_*` jump stubs
   into `CDirectSoundStream_*` functions and changes no other match.)
3. By hand: `XInputGetCapabilities` dropped (the constants match at `0x25DB04` is device-open
   code; `XInputOpen` is `0x25900D`); `D3D_pDevice` `0x212E70` and `D3D_DirtyFlags` `0x20FC28`
   read from the D3D code.

Result after M0: 129 of 248 functions (69 from step 1 after step 3's drop, 60 from step 2), 8 of
13 data, 119 at 0. The boot work (2026-10-28 and 29, HANDOFF.md) added 28 functions and three data
addresses by hand, each with its proof: 20 are names the SDK's list lacked (mostly the DirectSound
methods the runtime now replaces), 8 were at 0. It set `IDirectSoundBuffer_SetRolloffCurve` back
to 0: the SDK's byte signature matched the SetConeAngles wrapper (thin wrappers differ only in their
masked call target, so a signature alone can't tell them apart; check the callee). Now 156 of 268
functions, 11 of 13 data; of the 112 at 0, 37 are networking and Xbox Live (Hunter links no XNET
library), the rest not found yet or not called.

### Render state numbering
4361 has 146 render states where 4831 has 166: no DepthClipControl, StippleEnable,
PresentationInterval, SampleAlpha or the unused slots. Deferred states start at 82 (4831: 92),
complex at 117 (136), and the states after SampleAlpha's slot at 139 (159). Proven in
`SetRenderStateNotInline` (`0x200C05`: below 82 simple, `0x200C29`: below 117 deferred), by 19
`SetRenderState_*` setters agreeing on the table base `0x20FE30`, and by `D3D_InitDefaultState`
setting states 57 to 145. Texture stage states are numbered as in 4831.

### XDK 4361 data layout
`config/xdk/4361/layout.toml`, every key proven at an address in Hunter's D3D, DSOUND and XPP
code. Many device offsets differ from 4831, for example the textures (`0xA78` vs `0xB38`), the
transforms (`0x750` vs `0x810`) and the render target (`0x2070` vs `0x21B4`); the relative layout
of the surfaces (render target, depth, back, front, auto depth) is the same. 4361 keeps one pending
gamma index (`+0x2A8C`) where 4831 keeps a flag per ramp, so `CDevice_GammaPending` has no 4361
value and gamma changes need a hook.

### Sections
| Name | VA | Virtual size | Notes |
|---|---|---|---|
| `.text` | `0x11000` | `0x1EFB40` | game code, CRT, Bink, libjpeg |
| `D3D` | `0x200B40` | `0x12348` | Direct3D 8 |
| `DSOUND` | `0x212EA0` | `0x2138C` | DirectSound |
| `D3DX` | `0x234240` | `0x8B50` | D3DX8 |
| `XGRPH` | `0x23CDA0` | `0x1E58` | XGraphics |
| `WMADECXM` | `0x23EC00` | `0x838` | WMA decoder (XMO) |
| `WMADEC` | `0x23F440` | `0x18D80` | WMA decoder |
| `XPP` | `0x2581C0` | `0x762C` | XAPI peripherals (pads, memory units) |
| `.rdata` | `0x25F800` | `0x3BF5C` | |
| `.data` | `0x29B760` | `0xF0C1C` | 0x19024 bytes on disc |
| `DOLBY` | `0x38C380` | `0x7180` | Dolby Digital encoder image (DSP) |
| `$$XTIMAGE` | `0x393500` | `0x155D0` | title image |

There is no DMUSIC section although the library is listed; strings such as "Atlas Sound DM:
Unable to initialize DirectMusic" show the engine's DirectMusic path. Whether it runs is open.

### Kernel imports
All 123 are implemented by the SDK at `91146ff`. `DbgPrint` (ordinal 8) is registered with a
direct `RegisterExport` call in `sdk/runtime/kernel/xboxkrnl.cpp` rather than the `KERNEL_*`
macros, which hid it from the first `xbeimports.py`; the 007 port's own override is not needed.

### The engine
High Voltage Software's Atlas engine: classes `HunterApp`, `HtHunterManager`,
`GmSaveGame` (saves signed with `XCalculateSignature*`, `saveimage.xbx`), text configs read from
the archives (`Chars\Chars.txt`, `Weapons\WeapTest.txt`, `Controls\Rumble.txt`,
`*Profile.txt`, `*Open.txt`). Up to four players (the game's co-op).
