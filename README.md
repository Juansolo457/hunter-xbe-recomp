# Hunter: The Reckoning - XBE Recomp

The original Xbox **Hunter: The Reckoning** (2002, High Voltage Software), statically recompiled
to run natively on **Windows**, then on the **Steam Deck** and Linux.

> Unofficial. **No game data included.** Bring your own Xbox disc. Releases, when there are any,
> are source only: the game's code is translated from your copy on your own machine.

## What it is

A **static recompilation**: the game's x86 code is translated to C++ ahead of time with
[Xbox XBE Recomp](https://github.com/TGP482/XboxXBE-Recomp), and the Xbox kernel and XDK
libraries (Direct3D 8, DirectSound, XAPI) are implemented at the API level on the host. Not an
emulator and not a decompilation. It follows the shape of
[007FRWL-XBERecomp](https://github.com/TGP482/007FRWL-XBERecomp), which is the bar this project
aims for: the console game with modern display, graphics and input options.

The route, as with [graw360-recomp](https://github.com/Juansolo457/graw360-recomp):
1. **Windows** with the SDK as it ships (Direct3D 12).
2. **Steam Deck** running the Windows build through Proton.
3. **Native Linux** with a Vulkan renderer.

## Status

**Boots to the main menu on Windows.** The intro movies play with sound and the menu shows;
nothing past the menu is tested yet. Hunter is built on XDK 4361, which the SDK doesn't ship: this
repo carries the 4361 layout as an overlay and a few SDK fixes meant for upstream.

- [docs/PLAN.md](docs/PLAN.md): goals, decisions, milestones
- [docs/HANDOFF.md](docs/HANDOFF.md): current state, where things live, next steps
- [docs/FINDINGS.md](docs/FINDINGS.md): what the disc and the XBE are
- [docs/SETUP.md](docs/SETUP.md): build from your own disc

## Supported disc

Hunter: The Reckoning (USA), `default.xbe` title id `56550007`, SHA-1
`39735b530002b4e2da4182042591ef6e68ee08a0`.

## Layout

```
sdk/        XboxXBE-Recomp (MIT), vendored, with XDK 4361 fixes for upstream
config/     game.toml: the recompiler's input for default.xbe; xdk/4361: the XDK overlay
src/        host code: common/ (game info, options), game/ (hooks over recompiled functions)
tools/      disc and XBE readers, the repository audit
docs/       plan, handoff, findings, setup
assets/     your game files (ignored)
generated/  the recompiled game code (ignored, never committed)
```

## Legal

- No game files, executables, generated code or keys are distributed. Before pushing, run
  `python -I tools/audit_repo.py`; CI runs it over every commit.
- Our code is MIT ([LICENSE](LICENSE)); the SDK is MIT, TGP482 ([NOTICE](NOTICE)).
- Hunter: The Reckoning belongs to its owners. Not affiliated with High Voltage Software,
  Interplay, Vivendi Universal, Paradox Interactive, White Wolf or Microsoft.

## Credits

- High Voltage Software: the game
- TGP482: [Xbox XBE Recomp](https://github.com/TGP482/XboxXBE-Recomp) and the ports built on it
- [XenonRecomp](https://github.com/hedge-dev/XenonRecomp), [xemu](https://github.com/xemu-project/xemu),
  [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded): the references the SDK credits
- [Zydis](https://github.com/zyantific/zydis), [toml++](https://github.com/marzer/tomlplusplus),
  [Dear ImGui](https://github.com/ocornut/imgui), [SDL](https://github.com/libsdl-org/SDL)
- Built with [Claude Code](https://claude.com/claude-code)
