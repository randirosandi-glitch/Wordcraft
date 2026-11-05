# Word-style keyboard shortcut inventory — initial status

## Existing engine shortcut infrastructure (verified at the pinned v0.15.0 source)

The pinned upstream already contains a centralized command/keymap foundation; do not build a competing dispatcher in the Android shell:

- `crates/engine/src/cmd.rs::registry()` constructs the semantic command registry from command modules.
- `crates/engine/src/keymap.rs::KeyMap` normalizes key chords, resolves user-assigned keys before built-in command shortcuts, handles removed/reassigned shortcuts and exposes `keys_for`.
- `crates/ui-egui/src/keys/shortcuts.rs::dispatch` resolves a chord against the registry and invokes the semantic command through `app.run`.
- `global_shortcuts` defines a focus guard for editor canvas, text fields, overlay widgets and modal/customize-keyboard dialog contexts.
- The engine keymap has unit tests for normalization, assignment overrides, removal, reset and malformed preference handling.

This is a reusable registry/dispatcher, but it is not yet proven to satisfy every requested Microsoft Word mapping. The current Android patcher adjusts Android event delivery and modifier/IME behavior; it does not add every missing Word command or prove every chord on device.

**Remaining implementation gap:** the handover's complete per-shortcut Android runtime matrix and context-by-context verification are still outstanding. The new registry contract test now verifies a representative set of mappings against the pinned engine's real command registry; that is source-level evidence, not proof of Android event delivery.

**Status policy:** a shortcut is not implemented merely because it is documented. `ENGINE VERIFIED` means the pinned engine keymap resolves the chord to the stated semantic command and the CI registry contract test asserts it. `NOT TESTED ON DEVICE` remains until the matching Android physical-key path is exercised on hardware. `NOT IMPLEMENTED` means no binding exists in the pinned engine.
| Group | Shortcut | Intended command | Status |
|---|---|---|---|
| File | Ctrl+N | New document | NOT TESTED |
| File | Ctrl+O | Open document | NOT TESTED |
| File | Ctrl+S | Save | NOT TESTED |
| File | Ctrl+Shift+S / F12 | Save As | NOT TESTED |
| File | Ctrl+P | Print | NOT TESTED |
| File | Ctrl+W / Ctrl+F4 | Close document safely | NOT TESTED |
| Edit | Ctrl+Z / Ctrl+Y | Undo / redo | NOT TESTED |
| Clipboard | Ctrl+X / Ctrl+C / Ctrl+V | Cut / copy / paste | NOT TESTED |
| Clipboard | Ctrl+Shift+V | Paste special / unformatted paste | NOT TESTED |
| Selection | Ctrl+A | Select all | NOT TESTED |
| Deletion | Ctrl+Backspace / Ctrl+Delete | Delete previous / next word | NOT TESTED |
| Character | Ctrl+B / Ctrl+I / Ctrl+U | Bold / italic / underline | NOT TESTED |
| Character | Ctrl+Shift+D / Ctrl+Shift+W | Double underline / words-only underline | NOT TESTED |
| Character | Ctrl+Shift+A / Ctrl+Shift+K | All caps / small caps | NOT TESTED |
| Character | Ctrl+= / Ctrl+Shift+= | Subscript / superscript | NOT TESTED |
| Character | Ctrl+Space | Clear character formatting | NOT TESTED |
| Character | Ctrl+Shift+C / Ctrl+Shift+V | Copy / apply formatting | NOT TESTED |
| Paragraph | Ctrl+L / Ctrl+E / Ctrl+R / Ctrl+J | Left / center / right / justify | NOT TESTED |
| Paragraph | Ctrl+M / Ctrl+Shift+M | Increase / decrease paragraph indent | NOT TESTED |
| Paragraph | Ctrl+T / Ctrl+Shift+T | Hanging indent / reduce hanging indent | NOT TESTED |
| Paragraph | Ctrl+1 / Ctrl+2 / Ctrl+5 / Ctrl+0 | Line and paragraph spacing | NOT TESTED |
| Paragraph | Ctrl+Q | Clear paragraph formatting | NOT TESTED |
| Lists | Ctrl+Shift+L | Default bullet list | NOT TESTED |
| Font | Ctrl+Shift+F / Ctrl+Shift+P | Focus font family / size control | NOT TESTED |
| Font | Ctrl+] / Ctrl+[ | Increase / decrease font size | NOT TESTED |
| Font | Ctrl+Shift+> / Ctrl+Shift+< | Next / previous preset font size | NOT TESTED |
| Styles | Ctrl+Alt+1 / 2 / 3 | Heading 1 / 2 / 3 | NOT TESTED |
| Styles | Ctrl+Shift+N | Normal style | NOT TESTED |
| Navigation | Left / Right / Up / Down | Character / visual-line movement | NOT TESTED |
| Navigation | Ctrl+Left / Ctrl+Right | Previous / next word | NOT TESTED |
| Navigation | Home / End / Ctrl+Home / Ctrl+End | Line/document boundaries | NOT TESTED |
| Selection | Shift+arrows, Ctrl+Shift+arrows | Extend selection | NOT TESTED |
| Selection | Shift+Home/End, Ctrl+Shift+Home/End | Select to line/document boundary | NOT TESTED |
| Navigation | PageUp / PageDown | Previous / next viewport | NOT TESTED |
| Find | Ctrl+F / Ctrl+H / Ctrl+G / F5 | Find / replace / go to | NOT TESTED |
| Find | Enter / Shift+Enter / Esc | Next / previous result / close transient UI | NOT TESTED |
| Table | Tab / Shift+Tab / Ctrl+Tab | Next cell / previous cell / literal tab | NOT TESTED |
| Lists | Tab / Shift+Tab / Enter / Backspace | Contextual list nesting and exit | NOT TESTED |
| Links | Ctrl+K | Insert/edit hyperlink | NOT TESTED |
| Review | Ctrl+Alt+M / Ctrl+Shift+E | Comment / Track Changes | NOT TESTED |
| Fields | Alt+Shift+D / Alt+Shift+T / F9 | Date / time / update fields | NOT TESTED |
| Function | F1 / F4 / F6 / F8 / F10 / F11 | Help / Repeat / pane focus / selection / KeyTips / next field | MIXED; see engine evidence below |
| Excluded | F7 | Indonesian proofing | NOT APPLICABLE — explicitly out of scope |

## Implementation requirements

- Build one context-aware registry with stable command IDs, semantic keys, modifier state, focus context, priority, availability predicate, handler, user-facing description, platform caveats and test ID.
- Resolve OS-reserved chords, modal dialogs, text fields, Find/Replace, table cells, list items, editor body, toolbar/menu focus and IME composition in a documented precedence order.
- Use the same semantic command for shortcut, toolbar, menu and touch.
- Preserve unmatched key input. Do not intercept during IME composition if doing so would corrupt it.
- Normalize left/right Ctrl and Shift; handle key-up, repeat, focus loss, pause/resume and Bluetooth disconnect.
- Do not register no-op shortcuts. Unsupported engine features remain NOT IMPLEMENTED or NOT APPLICABLE with a reason.
- Generate the help screen/documentation from the actual registry where practical.

## Required test IDs

Use stable IDs in the eventual registry, for example `KBD-EDIT-UNDO`, `KBD-CHAR-BOLD`, `KBD-NAV-WORD-LEFT`, `KBD-FIND-NEXT`, and `KBD-TABLE-NEXT-CELL`. The final test list must contain one test reference per registered shortcut and focus-context conflict.


## Verified built-in engine bindings (pinned WordCraft v0.15.0)

The following mappings were read directly from the pinned source's `CommandSpec::key` declarations. `Mod` resolves to Ctrl on Android/Windows. Mappings asserted by `tests/word_shortcut_contract.rs` are **ENGINE VERIFIED + NOT TESTED ON DEVICE**; the remaining rows retain their own status below. No row is a physical-device PASS.

| Requested chord / behavior | Pinned engine command | Status / caveat |
|---|---|---|
| Ctrl+N / O / S / P / W | `file.new/open/save/print/close` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+F4 | `file.close` via Mod+F4 | IMPLEMENTED + NOT TESTED ON DEVICE |
| F12 Save As | `file.saveAs` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+S Save As | Bound to `styles.apply` (Apply Styles), not Save As | CONFLICT — not implemented as Save As; F12 / Alt+F2 invoke Save As |
| Ctrl+Tab switch document | No matching binding found | NOT IMPLEMENTED |
| Ctrl+Z / Ctrl+Y | `edit.undo/redo` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+X / C / V | `edit.cut/copy/paste` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+C / Ctrl+Shift+V | `edit.copyFormat/pasteFormat` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Alt+V | `edit.pasteSpecial` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+Alt+V | `edit.pasteText` (keep text only) | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+A | `select.all` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Backspace / Ctrl+Delete | `text.deleteWordBack/deleteWordForward` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+B / I / U | `format.bold/italic/underline` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+D / W | `format.doubleUnderline/wordUnderline` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+A / K | `format.allCaps/smallCaps` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+= / Ctrl+Shift+= | `format.subscript/superscript` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Space | `format.resetChar` (Mod+Space on Android/Windows) | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+L / E / R / J | `para.alignLeft/alignCenter/alignRight/justify` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+M / Ctrl+Shift+M | `para.indent/outdent` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+T / Ctrl+Shift+T | `para.hangingIndent/removeHanging` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+1 / 2 / 5 | `para.single/double/oneAndHalf` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+0 | `para.addSpaceBefore` | IMPLEMENTED + NOT TESTED ON DEVICE; adds space before, not a general spacing dialog |
| Ctrl+Q | `para.reset` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+L | `para.bullets` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+F / P | `format.font/size` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+] / Ctrl+[ | `format.growFont1/shrinkFont1` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+> / Ctrl+Shift+< | `format.growFont/shrinkFont` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Alt+1 / 2 / 3 | `para.heading1/heading2/heading3` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+N | `para.normal` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Alt+Shift+S | `styles.pane` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Arrow/Home/End/PageUp/PageDown | `caret.*` bindings | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Left / Ctrl+Right | `caret.wordLeft/wordRight` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Home / Ctrl+End | `caret.docStart/docEnd` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Shift+arrows and Ctrl+Shift+arrows | Shift-variant dispatch extends caret commands | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+F / Ctrl+H | `edit.find/findReplace` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+G | `edit.findNext`, **not Go To** | CONFLICT — Go To is F5 or Ctrl+Alt+G |
| F5 | `edit.goto` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Tab / Shift+Tab | `text.tab/backTab` | IMPLEMENTED + NOT TESTED ON DEVICE; list/table focus context still needs device testing |
| Ctrl+Tab inside table | `text.insertTab` (Mod+Tab on Windows/Android) | IMPLEMENTED + NOT TESTED ON DEVICE; verify only when a table cell owns editor focus |
| Ctrl+K | `insert.link` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Alt+M | `review.newComment` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Ctrl+Shift+E | `review.trackChanges` | IMPLEMENTED + NOT TESTED ON DEVICE |
| Alt+Shift+D / Alt+Shift+T | `insert.dateField/timeField` | IMPLEMENTED + NOT TESTED ON DEVICE |
| F9 | `references.updateFields` | IMPLEMENTED + NOT TESTED ON DEVICE |
| F12 | `file.saveAs` | IMPLEMENTED + NOT TESTED ON DEVICE |
| F6 Cycle panes | No matching binding found | NOT IMPLEMENTED |
| F8 Selection extension mode | `select.extend` | ENGINE VERIFIED + NOT TESTED ON DEVICE |
| F10 menu focus | Only Shift+F10 context-menu handling is present | NOT IMPLEMENTED as plain F10 |
| F11 Next field | `view.fullScreen` currently owns F11; Word's next-field behavior conflicts and is not bound. Alt+F1 is Next Field | NOT IMPLEMENTED (Word parity conflict) |
| Insert overtype | No editor overtype command/binding found | NOT IMPLEMENTED |
| F7 Indonesian proofing | Explicitly excluded by project scope | NOT APPLICABLE |

### Important mapping conflicts

- **Ctrl+G:** the engine assigns it to Find Next. The handover requests Go To. Preserve the current built-in mapping unless a deliberate, documented reassignment is approved; F5 and Ctrl+Alt+G already invoke Go To.
- **Ctrl+Shift+S:** WordCraft binds this to `styles.apply` (Apply Styles), matching the standard Word command. Save As is F12 / Alt+F2 on Windows. Do not reassign it to Save As.
- **Ctrl+Shift+V:** in WordCraft it applies copied formatting. Paste Special is Ctrl+Alt+V; keep-text-only is Ctrl+Shift+Alt+V. Do not relabel these commands.
- **Ctrl+0:** the command adds space before a paragraph; verify its toggle semantics before claiming exact Microsoft Word parity.

This source mapping narrows implementation work, but Android event delivery, focus contexts, modifier state and actual editor effects still require automated and physical-device regression tests.


## Microsoft Word 365 compatibility note (official documentation checked 2026-11-05)

The handover's shortcut table mixes legacy Word mappings with current Word 365 behavior. Microsoft's current Windows shortcut reference applies to Microsoft 365, Word 2024, 2021, 2019 and 2016, and explicitly notes that its key examples use a US keyboard layout. The current reference lists:

- Ctrl+G = Go To (WordCraft's pinned engine currently assigns Ctrl+G to Find Next).
- Ctrl+Shift+V = Paste Text Only; Ctrl+Alt+C / Ctrl+Alt+V = Copy/Paste Formatting (WordCraft currently uses Ctrl+Shift+C / Ctrl+Shift+V for formatting, Ctrl+Alt+V for Paste Special, and Ctrl+Shift+Alt+V for keep-text-only).
- Ctrl+Shift+S = Apply Styles (WordCraft already maps this to `styles.apply`; it is not Save As).
- Ctrl+0 = return zoom to 100% (WordCraft currently maps it to `para.addSpaceBefore`).
- Ctrl+Tab in a table inserts a tab character; the pinned engine maps Mod+Tab to `text.insertTab`.
- F4 repeats the last action (`edit.repeat`), F8 extends selection (`select.extend`), F9 updates fields (`references.updateFields`), and F11 toggles full screen (`view.fullScreen`) in the pinned engine. F6 cycles focus among document/panes/ribbon/status bar and F10 activates KeyTips; neither has a plain-key binding. Word's F11 next-field behavior conflicts with WordCraft's current full-screen binding.

**Do not silently mix profiles.** The current source mapping above is what the pinned engine actually does; the Microsoft reference above is what current Word documents. The original handover's Ctrl+Shift+C/V formatting behavior is a legacy-compatible choice, not the current Word 365 default.

Until the product shortcut profile is confirmed, keep the existing engine bindings unchanged and report the differences as conflicts. The next keyboard implementation pass must choose one coherent target profile and then update the engine registry, tests and help reference together.

Official reference: [Microsoft Support — Keyboard shortcuts in Word](https://support.microsoft.com/en-us/accessibility/word/keyboard-shortcuts-in-word) (Windows section; consulted 2026-11-05).


## Automated registry contract test

File: \`tests/word_shortcut_contract.rs\`

The test is copied into the exact pinned WordCraft \`wordcraft-engine\` test suite during CI and exercises the real \`cmd::registry()\` and \`KeyMap::resolve()\` APIs. It covers document operations, undo/redo, clipboard, deletion, character and paragraph formatting, font controls, heading styles, navigation, find/replace/go-to, table-tab insertion, hyperlinks, comments, Track Changes and date/time fields. A second test locks down intentional mapping differences (Ctrl+G, Ctrl+Shift+S, Ctrl+Shift+V) and explicitly verifies F4 Repeat, F8 Extend Selection, F9 Update Fields and the existing F11 Full Screen binding while checking that F6/F10 remain unbound.

**What PASS means:** a tested chord resolves to the expected semantic command in the pinned engine registry. It does not prove Android KeyEvent delivery, that the command succeeds in every document context, UI focus behavior, or physical-device behavior. Those remain separate tests. No no-op shortcut has been added.


## Registry contract CI result — run #65

Both tests in \`tests/word_shortcut_contract.rs\` passed against the exact pinned WordCraft v0.15.0 engine registry. This verifies chord-to-command resolution for the tested bindings and the documented current conflicts. It is not evidence of Android key event delivery or physical-device behavior.

Current function-key evidence: F4 = \`edit.repeat\`; F8 = \`select.extend\`; F9 = \`references.updateFields\`; F11 = \`view.fullScreen\` (conflicts with Word's next-field behavior); F6 and F10 are unbound in the pinned registry.
