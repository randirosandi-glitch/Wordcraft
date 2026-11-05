# Android source selection — 2026-11-05

## Decision

**Provisional foundation: official `storytold/wordcraft` engine + the existing Android build/integration layer from `MostafaXS1/artcraft-android`, pinned and adapted in this repository.** Do not import a third-party APK or wholesale-replace the current Android layer. Retain the current repository's guarded local patches and require the keyboard/device test matrix before calling the result stable.

This is a source-selection decision for the next engineering phase, not a claim that the current Android keyboard implementation has passed physical-device testing.

## User repository baseline and migration branch

- Repository: https://github.com/randirosandi-glitch/Wordcraft
- Default branch: `main`
- Main baseline: `03d64531a40824e944336e059ba6b017b4c5ede7`
- Existing advanced branch: `fix/wordcraft-font-proofing-sync-performance`
- Advanced branch HEAD: `5f9ad9fcc44f5d160af8698138cfcef06f939dc7`
- Advanced branch is 13 commits ahead of main, with no commits behind main at comparison time.
- Safe working branch created: `migration/stable-android-base`, fast-forwarded from main to the advanced branch HEAD. No branch history was rewritten and no existing branch was deleted.
- Current repository is a build/patch workspace, not a complete vendored WordCraft source tree. It contains the Android workflow, a guarded source patcher, icon assets, and README.

## Candidate evidence

| Candidate | Latest inspected commit | Android evidence | Main concern |
|---|---|---|---|
| Official engine — https://github.com/storytold/wordcraft | `3f555bc85dc9cc742ddae9f287cfc7b93a87480b`, 2026-11-04 | Actively maintained Rust workspace; current HEAD reports version 0.15.1; extensive DOCX and document-engine test tree | Not an Android shell by itself |
| ArtCraft Android builder — https://github.com/MostafaXS1/artcraft-android | `fbb4f66fcc868afdd8303d5227aa81db6a21d7fa`, 2026-10-27 | Current repository workflow pins this builder; contains IME, SAF, font, touch/trackpad and Android activity adapters; current CI run builds ARM64 APK | User previously reported keyboard defects with an earlier ArtCraft APK; current physical-device behavior remains unverified |
| ArtCraft Android fork — https://github.com/artcraft-android/wordcraft-android | `b2b7cf913c` (short SHA from inspected commit listing), 2026-10-28 | Active Android-specific source tree and CI/release workflow | No verified WordCraft-specific keyboard test evidence retrieved in this audit |
| Kanaaka Android port — https://github.com/kanaaka/wordcraft-android | `5f0ed9162c19a5b4904545ef2667885fe83d84d2`, 2026-10-13 | Detailed port notes; Ctrl tracker checks physical as well as logical key; Ctrl+A/Ctrl+B verified on Android 15 emulator; 4 shell tests reported passing | Based on upstream WordCraft 0.5.0; old relative to current 0.15.x engine; no automated device suite |
| Nideta Android branch — https://github.com/nideta231/wordcraft/tree/android | `7f960b2447a9d2ad2deabe6b6399548c94601c7c`, 2026-10-16 | WordCraft 0.7.0 Android shell; derived from Kanaaka shell; includes modifier, picker, touch-scroll, preferences and update-check modules | No newer commits found on inspected android branch; still behind current upstream; Android behavior not independently verified here |

Additional repository search found several similarly named ports/forks. They were not promoted to finalists without evidence that they are maintained Android ports of this exact WordCraft codebase.

## Weighted scorecard

Scores are 0–5. A score reflects retrieved source and build evidence, not README claims alone. The scorecard is preliminary because no physical Android device was available to this audit.

| Criterion | Weight | ArtCraft builder | Kanaaka | Nideta Android | Official engine alone |
|---|---:|---:|---:|---:|---:|
| Keyboard/shortcuts | 25% | 3.0 | 4.0 | 3.0 | 2.0 |
| Android input/IME/lifecycle | 15% | 4.0 | 3.5 | 3.5 | 1.0 |
| DOCX/document integrity | 15% | 4.0 | 2.5 | 3.5 | 5.0 |
| Storage/SAF/save/recovery | 10% | 4.5 | 2.5 | 2.5 | 1.0 |
| Build reproducibility/CI | 10% | 4.5 | 4.0 | 3.5 | 5.0 |
| Maintenance/upstream activity | 10% | 3.5 | 2.0 | 2.0 | 5.0 |
| Fonts/rendering | 5% | 4.0 | 3.0 | 3.5 | 4.0 |
| Touch/trackpad/mouse | 5% | 4.0 | 3.5 | 3.0 | 2.0 |
| License/maintainability | 5% | 3.5 | 4.0 | 4.0 | 5.0 |
| **Weighted total / 5** | **100%** | **3.73** | **3.25** | **3.10** | **3.05** |

### Score rationale and confidence

- **ArtCraft builder — 3.73, medium confidence:** the actual user workflow pins this builder at `fbb4f66...`, pins the WordCraft v0.15.0 source commit, patches the Android input path, and successfully completed a full CI ARM64 build and artifact verification. The builder has substantial Android-specific IME, SAF and font code. Keyboard score is deliberately reduced because of the user's earlier negative experience and because the current build has not passed the user's physical keyboard test matrix.
- **Kanaaka — 3.25, medium confidence:** strongest retrieved explicit Ctrl-modifier evidence: its port notes explain the logical/physical Control-key mismatch and report Ctrl+A/Ctrl+B working on Android 15 emulator. It also reports 4/4 shell tests and an independently verified signed ARM64 APK. Its upstream pin is WordCraft 0.5.0, and the repository's last inspected commit is 2026-10-13.
- **Nideta — 3.10, low-to-medium confidence:** source shows a dedicated Android shell on WordCraft 0.7.0 and modules for modifiers, file picker, touch scrolling and preferences. It is a useful implementation reference, but its Android branch has not moved since 2026-10-16 in the inspected history and device evidence was not independently confirmed.
- **Official engine alone — 3.05, high confidence for engine maintenance, low for Android:** upstream is very active and contains broad document/DOCX/font tests, but it does not provide the required Android integration by itself.

## Selection and rejection

1. Keep official WordCraft as the document engine and preserve its upstream version pin until a separately tested upgrade is ready.
2. Keep the existing ArtCraft Android integration as the working Android adapter because it is already integrated into the user's repository and has a reproducible CI path with SAF/IME/font work.
3. Do not treat ArtCraft v0.4.1 or any APK as the source of truth. Audit the exact current source revision and every local patch.
4. Use Kanaaka's modifier tracker and documented emulator test as a reference implementation for checking modifier handling; do not downgrade the engine to v0.5.0 merely to reuse the shell.
5. Use Nideta's v0.7.0 shell as a secondary reference for modular Android architecture, not as the selected base.
6. Do not import the entire ArtCraft Android repository into the user repository until its license, source boundaries, generator patches and current keyboard behavior are audited.

## Outstanding verification before final acceptance

- Inspect the complete builder license and all transitive vendored notices.
- Reproduce keyboard tests on the target physical tablet and Bluetooth keyboard.
- Verify exact current workflow patch output against the checked-in patcher.
- Build from a clean checkout of the migration branch and retain full logs.
- Compare DOCX round-trip behavior and SAF provider behavior on device.
- Audit all generated shortcut mappings against the live command registry.
