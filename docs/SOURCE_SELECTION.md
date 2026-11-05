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


## Additional candidates found in broader repository search

These were discovered after the initial shortlist and checked far enough to determine whether they were relevant to this product:

| Candidate | Latest inspected commit | Finding | Decision |
|---|---|---|---|
| https://github.com/tiborequiem/Wordcraft-Android | `baff023204`, 2026-10-29 | Native Rust Android port with a custom touch gesture state machine, SAF and IME viewport work; README claims v0.10.0 and ARM64 | Keep as a touch/SAF reference. Not selected until physical keyboard tests, exact build evidence and source-level keyboard routing are verified; stated emphasis is touchscreen behavior rather than keyboard-first tablet use |
| https://github.com/Murdock011/custom-wordcraft-android | `45f66110ce`, 2026-11-04 | Android native host and phone UI on WordCraft 0.15.0; README explicitly warns that code was AI-written, not reviewed line-by-line, and only lightly tested on an emulator and one Samsung phone | Reject as foundation for now. The maintainer's own warning is a material reliability risk; it also carries proofing-related work outside this project's scope |
| https://github.com/congduan/wordcraft-android | `89ced021f6`, 2026-10-18 | WordCraft-derived Android shell with mobile-first command sheets, SAF open and soft-input lift | Keep as a UI reference, not the selected keyboard-first tablet base; no independently verified physical keyboard matrix found |
| https://github.com/KR1901/wordcraft-android | `245edeee08`, 2026-10-31 | README describes a Jetpack Compose writing assistant and a custom software keyboard, not a port of the WordCraft document engine | Exclude as a false-positive name match; it is not the requested WordCraft editor |
| https://github.com/galiehneh/wordcraft-android | `b4cf72bc78`, 2026-10-16 | Android project with Gradle/Compose-style root rather than the same NativeActivity Rust port architecture | Not promoted without evidence of compatibility with the official WordCraft engine and required desktop editing workflow |

The wider search does not change the provisional selection. It does strengthen the decision not to choose a phone-first UI or an unreviewed fork for a tablet whose primary workload is serious document editing with a physical keyboard.
