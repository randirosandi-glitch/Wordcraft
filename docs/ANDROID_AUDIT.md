# Android architecture and defect audit — initial pass

## Repository structure observed

The user's repository is a build workspace rather than a full source fork. Its inspected tree at `5f9ad9fcc44f5d160af8698138cfcef06f939dc7` contains:

- `.github/workflows/android-apk.yml`
- `scripts/patch_wordcraft_android.py`
- `assets/android-icon-pack/`
- `assets/wordcraft-icon.svg`
- `README.md`

The workflow checks out a pinned Android builder, checks out WordCraft v0.15.0 at an exact commit, applies local Android compatibility changes, and packages an ARM64 APK.

## Input path — observed architecture

The builder provides a generated Android Activity and JNI bridge. Its source includes an Android IME bridge that drains queued commit/composition/delete events into egui input events, a SAF bridge that stages document-provider content and remembers destination URIs, and Android system-font discovery code. The user repository patcher modifies the generated Activity to distinguish physical keyboard events from virtual IME synthesized events and to guard against duplicate cross-callback Space/Enter input.

The conceptual path to verify on device is:

Physical keyboard → Android KeyEvent/GameActivity queue → winit Android backend → egui RawInput → WordCraft UI/editor command or text input → document state → render/dirty/save.

Soft keyboard → Android InputConnection → generated Activity queue → IME bridge → egui composition/commit/delete events → focused editor → render/dirty/save.

The exact current generated Rust/Java source after patching must be inspected from the workflow artifact/workspace before claiming every edge is proven.

## Defects and evidence

| Area | Evidence from source/workflow | Current status | Next proof |
|---|---|---|---|
| Physical key duplication | Local patcher separates physical hardware events from virtual-IME synthesized events | NOT TESTED on physical device | Type letters, Backspace, Delete, Space and Enter with Bluetooth keyboard; verify no missing/double input |
| Ctrl modifier handling | Kanaaka reference identifies missing logical Control mapping and checks physical key; local builder implementation still needs equivalent end-to-end audit | NOT TESTED | Test left/right Ctrl, Ctrl+A/C/V/X/S/Z/Y/B/I/U and held modifiers across frames |
| IME composition | Builder has queued IME bridge and input translation | NOT TESTED | Gboard composition, dead keys, combining marks, CJK input, cursor movement during composition |
| Open file delay | Main contains a commit titled “Wake Android native loop when SAF open results arrive”; advanced branch includes this work | NOT TESTED on device | Select file; verify parse/render without a second touch; repeat after resume/rotation |
| SAF open/save | Builder SAF bridge stages files and maps destination URIs; current CI build passes | NOT TESTED on physical provider | Open/edit/save/reopen local, Drive, Downloads and external provider documents |
| Drive repeated errors | Builder contains provider/SAF integration; no runtime evidence yet proves repeated popups are resolved | NOT TESTED | Offline, expired permission, token/network failure; verify quiet status/backoff and local editing |
| Font discovery | Builder has Android system-font module and user font directory logic | NOT TESTED | Compare picker list with installed system fonts; search Times New Roman; verify actual render and DOCX round-trip |
| Two-finger/trackpad | Existing advanced branch contains two-finger and trackpad scrolling commits; builder has Android input classification | NOT TESTED on physical hardware | Scroll without text selection; horizontal/vertical trackpad; mouse wheel and right-click |
| DOCX integrity | Upstream engine has a broad DOCX test tree; no current Android end-to-end round-trip evidence | NOT TESTED | Open/edit/save/reopen representative DOCX files and compare formatting |
| Autosave/recovery | Builder changelog describes SAF mirroring/autosave in its shared framework; current WordCraft-specific behavior still needs proof | NOT TESTED | Force-stop during edit, process death, provider failure and recovery |

## CI evidence

GitHub Actions run #60 (run ID `41941838011`) on code commit `2f7ff82c1ab3b89af3ab8ceeae547ca16689b495` completed successfully. Its build job passed source checkout, Android builder checkout, Winit alignment, exact WordCraft source checkout, patcher execution, SDK/NDK/Rust setup, APK build, signature/alignment/package/ARM64 verification and artifact upload. APK SHA-256: `c1b93a514470ac69b9848c21589648bbb46be13fa4bf2c89201d9cdd022a3847`.

This is a CI build PASS, not a runtime or physical-device PASS. The artifact was downloaded and its checksum independently matched the CI log.

## Known scope decision

Indonesian spell-checking, grammar-checking and proofing dependencies are explicitly OUT OF SCOPE and must not be reintroduced. Font enumeration and font-picker correctness remain in scope and are independent of proofing.

## Audit limitations

This is an initial source-based audit. No physical device session, Android emulator session, APK installation, DOCX round-trip, Google Drive provider test or runtime keyboard test was executed during this pass. Unknown root causes remain hypotheses until reproduced with logs.


## Shortcut registry contract automation

\`tests/word_shortcut_contract.rs\` is injected into the exact pinned WordCraft engine test suite by CI. It checks actual \`cmd::registry()\` and \`KeyMap::resolve()\` mappings and known conflicts. A passing contract proves chord-to-command registration only; it does not prove Android KeyEvent delivery, handler outcomes in all contexts, IME coexistence or physical-device behavior.
