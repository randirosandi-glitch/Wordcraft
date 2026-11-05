# WordCraft Android release checklist

## Existing CI build evidence

- [x] GitHub Actions run #55 completed successfully.
- [x] Exact WordCraft source pin was checked by the workflow.
- [x] ARM64 build step passed.
- [x] APK verification step passed for signature, alignment, package ID and ARM64.
- [x] Artifact upload step passed.
- [x] Downloaded the latest exact APK artifact and independently recomputed its SHA-256; it matches the CI log.
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


## Latest verified CI build — run #60

- Workflow: https://github.com/randirosandi-glitch/Wordcraft/actions/runs/41941838011
- Run ID: \`41941838011\`; job ID: \`126964317213\`
- Code commit built: \`2f7ff82c1ab3b89af3ab8ceeae547ca16689b495\`
- Migration branch HEAD at this documentation update: \`3ef064100e5b95f94f70d329936863a3a27bb733\`
- Artifact: \`wordcraft-artcraft-android-arm64\`; ID: \`13377645613\`; ZIP size: \`63,156,756\` bytes
- Artifact expiry: 2026-11-19 00:39:31 UTC
- APK file: \`wordcraft-android-arm64.apk\`; size: \`134,238,478\` bytes
- Package: \`ai.storyteller.wordcraft\`; versionName: \`0.15.0\`; versionCode: \`16781056\`
- ABI: \`arm64-v8a\`; native library: \`lib/arm64-v8a/libwordcraft_android.so\`
- APK Signature Scheme v2: PASS; zipalign: PASS; APK archive integrity: PASS
- Signer: temporary builder certificate \`CN=ArtCraft Android Builder, OU=Local Builds, O=ArtCraft, C=US\`
- Signer certificate SHA-256: \`17bebc68e49a4f472eb29fa38c56de50ef0685105a89ed110abfe569f1ce0c99\`
- APK SHA-256: \`c1b93a514470ac69b9848c21589648bbb46be13fa4bf2c89201d9cdd022a3847\`
- Artifact ZIP SHA-256: \`19813300bf5d0088942337ae8e50e4ab4788b2c8349acf6a23b75d940ee7747c\`
- The ZIP and APK were downloaded/extracted in this session; local APK SHA-256 matches the build log exactly.

**Release limitation:** this is a verified CI/debug artifact, not a persistent production-signed update. The temporary signer is not proven to match the certificate on the installed app. Do not uninstall the existing app just to install this APK; preserve user data until signing continuity or a safe backup/restore route is established.

## Final device acceptance status

- [ ] Install/upgrade on target tablet — NOT TESTED
- [ ] Launch and verify no fatal startup error — NOT TESTED
- [ ] Physical/Bluetooth keyboard and IME matrix — NOT TESTED
- [ ] SAF / Google Drive save-and-reopen round trip — NOT TESTED
- [ ] DOCX format round trip — NOT TESTED
- [ ] Times New Roman/system font discovery and rendering — NOT TESTED
- [ ] Trackpad/touch/mouse matrix — NOT TESTED
