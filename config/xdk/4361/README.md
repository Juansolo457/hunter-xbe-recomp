# XDK 4361 overlay

Hunter: The Reckoning is built on XDK 4361; the SDK ships `sdk/xdk/4831` and `sdk/xdk/5849`
only. This folder holds what the SDK needs for 4361, in the same format as those folders:

- `layout.toml`: the XDK data layouts the runtime reads, each key proven at an address in
  Hunter's code (see `sdk/xdk/4831/layout.toml` for the keys and the comment style).
- `signatures.toml`: written by `xbe_symbols --sign config/game.toml --out
  config/xdk/4361/signatures.toml` once `config/game.toml` is complete by hand.

Neither exists yet (M0 in docs/PLAN.md). When both are complete they go to
TGP482/XboxXBE-Recomp as a pull request, so later 4361 titles get them from the SDK.
