# Physical-device and emulator test matrix

Status values: PASS, FAIL, NOT TESTED, BLOCKED, NOT APPLICABLE.

| Device | Android | Keyboard/input | Scenario | Status | Evidence / notes |
|---|---|---|---|---|---|
| Target user tablet | NOT RECORDED | Bluetooth keyboard, exact model/layout NOT RECORDED | Basic letters, numbers, punctuation, symbols | NOT TESTED | Must be executed on physical hardware |
| Target user tablet | NOT RECORDED | Bluetooth keyboard | Backspace/Delete, key repeat, Enter, Tab, Space | NOT TESTED | Check missing and duplicate characters |
| Target user tablet | NOT RECORDED | Bluetooth keyboard | Left/right Ctrl, Shift, Alt; Ctrl+A/C/V/X/S/Z/Y/B/I/U | NOT TESTED | Test press/release and held modifier across frames |
| Target user tablet | NOT RECORDED | Soft keyboard / IME | Composition, dead keys, combining marks, Unicode and cursor edits | NOT TESTED | Verify composing/commit/delete paths |
| Target user tablet | NOT RECORDED | Touch | One-finger caret/selection and two-finger scroll | NOT TESTED | Scroll must not select text |
| Target user tablet | NOT RECORDED | Trackpad / mouse | Horizontal/vertical scroll, click, drag, right-click, wheel | NOT TESTED | Record device source/tool classification |
| Target user tablet | NOT RECORDED | SAF provider | Select/open file without a second touch | NOT TESTED | Repeat after app resume and rotation |
| Target user tablet | NOT RECORDED | SAF / DOCX | Edit, save, close and reopen | NOT TESTED | Verify formatting and destination URI |
| Target user tablet | NOT RECORDED | Fonts | Search Times New Roman, inspect system list, render and reopen | NOT TESTED | Picker name and actual rendered face must agree |
| Android 15 emulator | Android 15 | Emulator keyboard | Kanaaka reference reports Ctrl+A and Ctrl+B tested | NOT TESTED BY THIS PROJECT | External candidate evidence only; not a PASS for this build |

Do not copy the Kanaaka emulator result into this project's PASS column. Emulator success does not establish physical Bluetooth keyboard, trackpad, IME or provider behavior.
