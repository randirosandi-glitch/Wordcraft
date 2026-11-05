# WordCraft Android — integration workspace

This repository builds and maintains the Android adaptation of the official WordCraft document engine. Source selection, provenance, architecture audits, shortcut status and release evidence are maintained in `docs/`.

## Current source inputs

- **WordCraft engine:** https://github.com/storytold/wordcraft
  - Current CI pin: v0.15.0
  - Commit: `b47079fc791595fd84bb499d64dcd3f0624ef35a`
- **Android builder / platform integration:** https://github.com/MostafaXS1/artcraft-android
  - Current CI pin: `fbb4f66fcc868afdd8303d5227aa81db6a21d7fa`
- **Winit alignment:** https://github.com/storytold/winit
  - Commit: `a517b3846ee8457d84ee4975110bfda6797c44dc`
- **Android package:** `ai.storyteller.wordcraft`
- **Target ABI:** `arm64-v8a`

The builder is an input/source dependency, not the final owner of this product. Local Android compatibility patches and the final build workflow are maintained here. Do not copy or rename a third-party APK.

## Build workflow

GitHub Actions checks out the exact builder and engine revisions, aligns the pinned Winit source, applies guarded local changes from `scripts/patch_wordcraft_android.py`, builds the ARM64 APK, verifies package/signature/alignment/ABI and uploads the artifact.

The workflow can be started from **Actions → Build WordCraft Android → Run workflow**. Pushes to `main`, `fix/**` and `migration/**` also run the build.

CI PASS proves the build and the checks that the workflow actually executes. It does not prove physical Bluetooth keyboard, IME, trackpad, SAF provider or DOCX round-trip behavior. See `docs/DEVICE_TEST_MATRIX.md`.

## Engineering rules

1. Keep the official WordCraft engine as the document model and command source unless a documented, tested source-selection decision changes it.
2. Do not import an Android port wholesale without reviewing its code, dependency graph, provenance and license obligations.
3. Preserve all existing branches and known-good artifacts. Never force-push or rewrite history.
4. Use guarded patch anchors; fail closed when expected source changes.
5. Do not register no-op shortcuts. Shortcut status must reflect a real semantic command and a passing relevant test.
6. Indonesian spell-checking, grammar-checking and proofing are explicitly out of scope. Font discovery remains in scope.
7. Do not call a build or feature physically verified without device evidence.

## Key documentation

- `docs/SOURCE_SELECTION.md` — candidate scorecard and foundation decision
- `docs/UPSTREAM_PROVENANCE.md` — exact upstream inputs and local adaptations
- `docs/ANDROID_AUDIT.md` — architecture and defect audit
- `docs/WORD_SHORTCUTS.md` — Word-style shortcut inventory and status
- `docs/IMPLEMENTATION_LOG.md` — work log and commit evidence
- `docs/DEVICE_TEST_MATRIX.md` — physical device/emulator tests
- `docs/RELEASE_CHECKLIST.md` — APK verification and release gates
