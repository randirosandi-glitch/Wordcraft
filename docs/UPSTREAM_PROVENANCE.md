# Upstream provenance

## Current build inputs

- Application repository: https://github.com/randirosandi-glitch/Wordcraft
- Android builder: https://github.com/MostafaXS1/artcraft-android
- Builder commit pinned by workflow: `fbb4f66fcc868afdd8303d5227aa81db6a21d7fa`
- WordCraft source release: `v0.15.0`
- WordCraft source commit pinned by workflow and patcher: `b47079fc791595fd84bb499d64dcd3f0624ef35a`
- Winit source alignment: `storytold/winit` commit `a517b3846ee8457d84ee4975110bfda6797c44dc`
- WordCraft Cargo lock also checks the egui fork `6d518fc799681571963842f95b55a6b68431b15a`.

## Local adaptation

- `scripts/patch_wordcraft_android.py` applies guarded source changes to the pinned WordCraft checkout and verifies expected dependency pins.
- `.github/workflows/android-apk.yml` checks out the builder and exact WordCraft source, aligns the vendored Winit source, runs the local patcher, builds the ARM64 APK, verifies package/signature/ABI and uploads the artifact.
- The workflow includes an additional `ImeResetCompleted` event adaptation and skips an obsolete scrolling hook for WordCraft because the current-source equivalent is applied by the local patcher.
- Existing project commits and branch history are retained; no third-party APK is copied or renamed.

## Licensing status

WordCraft upstream declares `MIT OR Apache-2.0` in its workspace manifest and contains both license files and attribution notices. The Android builder contains a license file and vendored components; the precise compatibility and notice obligations remain to be reviewed before any wholesale source import. Preserve every upstream and vendored license/NOTICE/attribution file.

## Future update procedure

1. Select an exact upstream WordCraft commit/tag and record it here.
2. Inspect dependency and Winit/egui pins before changing the version.
3. Rebase/review the local patcher against that exact source; guarded anchors must fail closed.
4. Run formatting, source tests and clean ARM64 build.
5. Verify APK package, ABI, signature and SHA-256.
6. Test the keyboard, IME, SAF, DOCX and fonts on physical Android hardware.
7. Update this document and `docs/IMPLEMENTATION_LOG.md` in the same change.
