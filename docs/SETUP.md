# Build from your own disc

This project ships **source only**. No download contains the game. The game's code is
translated from your own copy of the Xbox disc on your machine, and the game data comes from the
same disc. You need **Hunter: The Reckoning (USA)** for the original Xbox.

> Early days: nothing builds or runs yet. See [HANDOFF.md](HANDOFF.md) for where it stands.
> These steps describe the target and grow with each milestone.

## 1. Get the game files

Dump your disc to an ISO, then extract it into `assets/`:

```
python -I tools/xiso.py "<your disc>.iso" extract assets
```

This writes the whole disc into `assets/`: `default.xbe` and the `Media` folder beside it
(about 3.8 GB). A full disc dump works too; the tool finds the game partition. Check the XBE:

```
python -I tools/xbeinfo.py assets/default.xbe
```

It must print SHA-1 `39735b530002b4e2da4182042591ef6e68ee08a0`.

## 2. Build (Windows)

Install [Visual Studio 2022](https://visualstudio.microsoft.com/downloads/) with **Desktop
development with C++**, **C++ Clang tools for Windows** and **C++ CMake tools for Windows**
(`build.bat` offers to add the last two), then run `build.bat`. The first build recompiles the
game and takes a while. The exe is written to `out\build\release\Hunter.exe`.

It stops until XDK 4361 support lands (M0 in [PLAN.md](PLAN.md)).

## Steam Deck and Linux

The Deck runs the Windows build through Proton first. A native Linux build with Vulkan comes
last (M5 in [PLAN.md](PLAN.md)).
