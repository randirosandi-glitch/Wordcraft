# Implementation log

## 2026-11-05 — Handover execution / repository rebase baseline

- Read the complete WordCraft Master Technical Handover v2.
- Verified GitHub access to the user repository and candidate sources.
- Recorded user repository default branch `main` at `03d64531a40824e944336e059ba6b017b4c5ede7`.
- Inspected existing branch `fix/wordcraft-font-proofing-sync-performance` at `5f9ad9fcc44f5d160af8698138cfcef06f939dc7`; it is 13 commits ahead of main and has no commits behind main at comparison time.
- Created `migration/stable-android-base` from main and fast-forwarded it to the advanced branch HEAD. No force-push, history rewrite or deletion occurred.
- Inspected current build workflow and local guarded patcher. Current workflow pins ArtCraft builder `fbb4f66fcc868afdd8303d5227aa81db6a21d7fa`, WordCraft v0.15.0 source `b47079fc791595fd84bb499d64dcd3f0624ef35a`, and Winit `a517b3846ee8457d84ee4975110bfda6797c44dc`.
- Inspected official upstream, ArtCraft builder, Kanaaka Android port and Nideta Android branch.
- Retrieved CI run #55: run ID `41817364480`, commit `5f9ad9fcc44f5d160af8698138cfcef06f939dc7`, conclusion success. All 21 job steps completed successfully except the intentionally skipped failure-log upload step.
- Retrieved artifact metadata: `wordcraft-artcraft-android-arm64`, artifact ID `13315404034`, 63,156,762 bytes, not expired at inspection time.
- Added initial source-selection, provenance, Android audit, shortcut inventory and device/release status documents.

### Not yet done

- No source import or wholesale migration has been performed.
- No application source implementation has been changed in this phase.
- No physical device/emulator tests were run.
- No new APK was built in this session; the cited PASS is the existing GitHub Actions run #55.
- No final release or shortcut parity claim is made.


## 2026-11-05 — shortcut architecture inspection and CI branch enablement

- Verified the pinned WordCraft v0.15.0 source already has a centralized semantic command registry (`crates/engine/src/cmd.rs::registry`), keymap (`crates/engine/src/keymap.rs::KeyMap`) and UI shortcut dispatcher (`crates/ui-egui/src/keys/shortcuts.rs::dispatch`). This should be extended rather than duplicated in the Android shell.
- Confirmed keymap unit tests cover normalization, user override/removal/reset and malformed preferences. The complete requested Word-style chord inventory is not yet mapped/tested; documentation correctly retains NOT TESTED statuses.
- Updated README to match the actual workflow inputs and to distinguish CI build success from physical-device validation.
- Updated workflow push filters to include `migration/**`, so the isolated migration branch is built by CI rather than only the default/fix branches.
- Workflow run started for migration branch commit `543973e8568e011e6337482a91791533cf217ae7`; result pending at log update time.


## 2026-11-05 — pinned WordCraft shortcut mapping audit

- Read the exact WordCraft v0.15.0 pinned source, not only upstream HEAD.
- Confirmed the command registry already binds a broad set of Word-style shortcuts to semantic command IDs, including file operations, edit/clipboard, character and paragraph formatting, fonts, headings, navigation, find/replace, hyperlinks, comments, track changes and fields.
- Recorded exact command IDs and unresolved Android/device status in `docs/WORD_SHORTCUTS.md`.
- Found important mapping conflicts: Ctrl+G is Find Next (Go To is F5 or Ctrl+Alt+G); Ctrl+Shift+S is Apply Styles (Save As is F12 / Alt+F2); Ctrl+Shift+V is Paste Formatting (Paste Special is Ctrl+Alt+V; keep-text-only is Ctrl+Shift+Alt+V).
- These findings prevent incorrect shortcut claims and avoid rebinding established Word semantics.
- A dedicated automated keymap regression matrix is the next implementation step; until it is added and run, mappings remain NOT TESTED on device.

- Expanded the weighted scorecard to include the additional Tibor, Murdock and Congduan Android ports discovered in the broader search; rejected phone-first, unrelated and unreviewed candidates with explicit reasons.
- Corrected the Ctrl+Shift+S finding: the pinned engine binds it to Apply Styles, while Save As is F12 / Alt+F2 on Windows.


## 2026-11-05 — retrieved APK verification logs

- Downloaded the completed GitHub Actions job logs for run #55 (job `126531419395`).
- Confirmed build success, exact package ID `ai.storyteller.wordcraft`, versionName `0.15.0`, versionCode `16781056`, ABI `arm64-v8a`, and native library presence.
- APK signature verification passed using APK Signature Scheme v2; zipalign and ZIP integrity checks passed.
- Exact APK SHA-256: `824175c2fa5f0bbf31e575fe841d9d9c818ab4fbcd6d31532fcab2e4a6e8ecb0`.
- Artifact ZIP SHA-256: `366fa94282810d2fbcef040f42cee0e9b9c091351cae8ac0e6be6e492dc0ebc7`.
- Installation and launch on the user's physical device remain NOT TESTED.


## 2026-11-05 — migration APK retrieval and shortcut contract test

- Verified successful migration CI run #60 \`41941838011\`, job \`126964317213\`, for build commit \`2f7ff82c1ab3b89af3ab8ceeae547ca16689b495\`.
- Downloaded artifact \`wordcraft-artcraft-android-arm64\` (ID \`13377645613\`) and extracted the ARM64 APK.
- Independently recomputed APK SHA-256 \`c1b93a514470ac69b9848c21589648bbb46be13fa4bf2c89201d9cdd022a3847\`; it matches the CI build log. APK ZIP integrity also passed locally.
- CI reported package \`ai.storyteller.wordcraft\`, version \`0.15.0\`, ABI \`arm64-v8a\`, APK v2 signature verification and zipalign success.
- The builder uses an ephemeral signing certificate. Production signing-key continuity and physical-device upgrade remain unverified.
- Added \`tests/word_shortcut_contract.rs\`, a registry-level contract test against the exact pinned WordCraft engine. Added the CI step and a \`tests/**\` push path. The test run is pending the next workflow result; it does not simulate Android input or prove editor behavior.


## 2026-11-05 — shortcut contract correction from CI evidence

- The first CI execution correctly caught a false assumption: the pinned engine binds F4 to `edit.repeat` and F8 to `select.extend`.
- Updated the contract to assert those existing Word-style behaviors, and only treat F6, F10 and F11 as absent in the pinned registry.
- The first shortcut contract test's main mapping test passed; its second test failed solely on the incorrect assumption that F4 was unbound. The corrected contract is queued for a fresh CI run.


- Further source inspection confirmed F9 resolves to `references.updateFields` and F11 resolves to `view.fullScreen`; F11 is therefore a Word-parity conflict, not an absent binding. The contract now asserts both and only expects F6/F10 to be unbound.
