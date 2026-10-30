# How changes get into master

`master` is what everyone builds from, so nothing reaches it except through a pull request.
GitHub enforces this for everyone, the maintainer included: no direct pushes, no force pushes,
the branch can't be deleted, and a pull request merges only once the `audit` check passes, the
branch is up to date and every review conversation is resolved. GitHub doesn't require an
approving review; reviewing every pull request (CodeRabbit's, below) is this project's rule.

## The process

1. **Branch from `master`**, one branch per piece of work, named for it (`xdk-4361`,
   `vulkan-backend`). Contributors without write access fork the repository and branch there.
2. **Commit on the branch.** Keep commits focused, with messages that say what changed and why.
   Never commit game material: no game files, executables, archives, the recompiled code in
   `generated/`, logs or captures (see [Legal](README.md#legal)). Run
   `python -I tools/audit_repo.py` before pushing.
3. **Open a pull request into `master`.** Its description says what changed, what was built
   (Linux or Windows; say when it changes `sdk/`, which every build compiles), and what was
   tested in play and what wasn't.
4. **Before it can merge:**
   - the `audit` check passes (`.github/workflows/audit.yml`). It runs the same script over
     every commit (`--history`), so a file added and then deleted on a branch still fails it;
   - the branch is up to date with `master`;
   - every review conversation is resolved. CodeRabbit reviews each pull request
     (`.coderabbit.yaml`). Fix what holds up; answer what doesn't with the reason; then resolve
     the thread.
5. **Merge with a merge commit** (the "Create a merge commit" button), so a pull request's
   history stays together in `master`.

## The SDK

`sdk/` is a copy of [XboxXBE-Recomp](https://github.com/TGP482/XboxXBE-Recomp) pinned in
`sdk.toml`, kept as upstream ships it until the native Linux phase. Updating it from upstream is
a pull request of its own. Hunter's XDK 4361 data lives in `config/xdk/4361/` and goes upstream
as a pull request once complete.

## Releases

Releases are tagged on `master` once the pull requests that make them are merged. **They are
source only:** never attach builds, game files or test packages. Players build from their own
disc ([docs/SETUP.md](docs/SETUP.md)). The one exception to building locally is `release.bat`:
its `Hunter.zip` is for testing on your own machines (a Steam Deck, say) and is never attached to
a release.
