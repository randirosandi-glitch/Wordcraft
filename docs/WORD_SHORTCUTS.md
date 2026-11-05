# Word-style keyboard shortcut inventory — initial status

**Status policy:** a shortcut is not implemented merely because it is documented. Every IMPLEMENTED row requires a semantic editor command and a test. Current repository evidence does not yet prove the complete shortcut set. Therefore the inventory below marks shortcuts NOT TESTED until source-level handler mapping and automated tests are completed.

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
| Function | F1 / F4 / F6 / F8 / F10 / F11 | Help/repeat/panes/selection/menu/field navigation | NOT TESTED |
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
