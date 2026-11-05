# WordCraft Android release checklist

## Existing CI build evidence

- [x] GitHub Actions run #55 completed successfully.
- [x] Exact WordCraft source pin was checked by the workflow.
- [x] ARM64 build step passed.
- [x] APK verification step passed for signature, alignment, package ID and ARM64.
- [x] Artifact upload step passed.
- [ ] Download and independently inspect the exact APK artifact in this session.
- [x] Retrieved completed run #55 job logs and confirmed the exact APK SHA-256 and package metadata.
- [ ] Install and launch on the target physical device.
- [ ] Confirm persistent signing identity across builds.
- [ ] Complete critical keyboard/IME/SAF/DOCX/font tests on physical device.

## Artifact metadata from run #55

- Run: https://github.com/randirosandi-glitch/Wordcraft/actions/runs/41817364480
- Run ID: `41817364480`
- Commit: `5f9ad9fcc44f5d160af8698138cfcef06f939dc7`
- Artifact name: `wordcraft-artcraft-android-arm64`
- Artifact ID: `13315404034`
- Artifact size: 63,156,762 bytes
- Artifact expired: false at inspection time

## Before a release

- [ ] Confirm package ID and version code/name against the installed app.
- [ ] Confirm ARM64 ABI and APK archive integrity.
- [ ] Verify signature and signing-key continuity.
- [ ] Generate SHA-256 from the exact downloaded APK.
- [ ] Install/upgrade test without losing user documents.
- [ ] Launch and open a document.
- [ ] Run shortcut, IME, pointer, SAF, DOCX, font and recovery regression tests.
- [ ] Attach complete build logs, test report and APK to the release.
- [ ] Update source provenance and implementation log with exact commit SHAs.


## Exact APK verification from run #55

- Package: `ai.storyteller.wordcraft`
- Version: `0.15.0` (versionCode `16781056`)
- ABI: `arm64-v8a`
- Native library: `lib/arm64-v8a/libwordcraft_android.so`
- APK signing: APK Signature Scheme v2 verified
- ZIP integrity: passed
- zipalign: passed
- APK SHA-256: `824175c2fa5f0bbf31e575fe841d9d9c818ab4fbcd6d31532fcab2e4a6e8ecb0`
- Workflow artifact ZIP SHA-256: `366fa94282810d2fbcef040f42cee0e9b9c091351cae8ac0e6be6e492dc0ebc7`
- Evidence: [run #55](https://github.com/randirosandi-glitch/Wordcraft/actions/runs/41817364480), job ID `126531419395`.

This verifies the CI-produced APK archive and signing metadata. Installation and launch on the target physical tablet remain NOT TESTED.
