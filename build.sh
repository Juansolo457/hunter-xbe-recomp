#!/bin/bash
# build.sh: Hunter: The Reckoning on Linux (the Steam Deck first). The Linux path is being built
# milestone by milestone (docs/PLAN.md); each stage below says whether it exists yet.
#   ./build.sh            config check, then every stage that exists
# env: JOBS (default nproc), CXX (default clang++)
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"
XBE=assets/default.xbe
SHA1=39735b530002b4e2da4182042591ef6e68ee08a0

echo "Hunter: The Reckoning - Linux build"
if [ ! -f "$XBE" ]; then
    echo "Put the game files in assets/ first: default.xbe with its Media folder beside it."
    exit 1
fi
have=$(sha1sum "$XBE" | cut -d' ' -f1)
if [ "$have" != "$SHA1" ]; then
    echo "assets/default.xbe is not the supported USA release (sha1 $have)."
    exit 1
fi

# 1. XDK 4361 support: xbe_symbols needs sdk/xdk/4361/signatures.toml, or a config written by hand (M0)
if [ ! -f sdk/xdk/4361/signatures.toml ] && ! grep -q '^\[symbols\]' config/game.toml; then
    echo "[1/4] XDK 4361 support is not there yet (M0 in docs/PLAN.md): no config to recompile from."
    exit 1
fi
# 2. the recompiler on Linux (M0), 3. headless boot through sdk/harness (M1),
# 4. the Vulkan app (M2): not written yet
echo "[2/4] The Linux recompiler build is not written yet (M0 in docs/PLAN.md)."
exit 1
