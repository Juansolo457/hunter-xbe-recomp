# Build from your own disc

This project ships **source only**. No download contains the game. The game's code is
translated from your own copy of the Xbox disc on your machine, and the game data comes from the
same disc. You need **Hunter: The Reckoning (USA)** for the original Xbox.

> Early days: nothing builds or runs yet. See [HANDOFF.md](HANDOFF.md) for where it stands.
> These steps describe the target and grow with each milestone.

## 1. Get the game files

Dump your disc to an ISO, then extract it into `assets/`:

```
python -I tools/xiso.py "<your disc>.iso" assets
```

This writes the whole disc into `assets/`: `default.xbe` and the `Media` folder beside it
(about 3.8 GB). A full disc dump works too; the tool finds the game partition. Check the XBE:

```
python -I tools/xbeinfo.py assets/default.xbe
```

It must print SHA-1 `39735b530002b4e2da4182042591ef6e68ee08a0`.

## 2. Build

**Linux (the target, Steam Deck first):** clang, CMake, Ninja, the Vulkan headers and loader,
SDL3's build dependencies, then `./build.sh`. Not working yet: see PLAN.md for the milestones.

**Windows (the SDK as shipped, Direct3D 12):** Visual Studio 2022 with Desktop development with
C++, C++ Clang tools and C++ CMake tools, then `build.bat`. It stops until XDK 4361 support
lands (M0).
