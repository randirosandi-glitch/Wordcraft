# WordCraft Android release checklist

## Existing CI build evidence

- [x] GitHub Actions run #55 completed successfully.
- [x] Exact WordCraft source pin was checked by the workflow.
- [x] ARM64 build step passed.
- [x] APK verification step passed for signature, alignment, package ID and ARM64.
- [x] Artifact upload step passed.
- [ ] Download and independently inspect the exact APK artifact in this session.
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
