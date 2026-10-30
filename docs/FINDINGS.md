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
