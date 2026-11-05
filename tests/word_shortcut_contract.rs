use wordcraft_engine::{cmd, KeyMap};

/// Engine-registry contract test only; it does not simulate Android input events.
#[test]
fn word_style_shortcuts_resolve_to_real_engine_commands() {
    let registry = cmd::registry();
    let keymap = KeyMap::default();
    let bindings = [
        ("Mod+N", "file.new"), ("Mod+O", "file.open"), ("Mod+S", "file.save"),
        ("F12", "file.saveAs"), ("Alt+F2", "file.saveAs"), ("Mod+P", "file.print"),
        ("Mod+W", "file.close"), ("Mod+F4", "file.close"),
        ("Mod+Z", "edit.undo"), ("Mod+Y", "edit.redo"), ("Mod+Shift+Z", "edit.redo"),
        ("Mod+X", "edit.cut"), ("Mod+C", "edit.copy"), ("Mod+V", "edit.paste"),
        ("Mod+A", "select.all"), ("Mod+Backspace", "text.deleteWordBack"),
        ("Mod+Delete", "text.deleteWordForward"), ("Mod+B", "format.bold"),
        ("Mod+I", "format.italic"), ("Mod+U", "format.underline"),
        ("Mod+Shift+D", "format.doubleUnderline"), ("Mod+Shift+W", "format.wordUnderline"),
        ("Mod+Shift+A", "format.allCaps"), ("Mod+Shift+K", "format.smallCaps"),
        ("Mod+=", "format.subscript"), ("Mod+Shift+=", "format.superscript"),
        ("Mod+Space", "format.resetChar"), ("Mod+Shift+C", "edit.copyFormat"),
        ("Mod+Shift+V", "edit.pasteFormat"), ("Mod+Alt+V", "edit.pasteSpecial"),
        ("Mod+Shift+Alt+V", "edit.pasteText"), ("Mod+L", "para.alignLeft"),
        ("Mod+E", "para.alignCenter"), ("Mod+R", "para.alignRight"),
        ("Mod+J", "para.justify"), ("Mod+M", "para.indent"),
        ("Mod+Shift+M", "para.outdent"), ("Mod+T", "para.hangingIndent"),
        ("Mod+Shift+T", "para.removeHanging"), ("Mod+1", "para.single"),
        ("Mod+2", "para.double"), ("Mod+5", "para.oneAndHalf"),
        ("Mod+0", "para.addSpaceBefore"), ("Mod+Q", "para.reset"),
        ("Mod+Shift+N", "para.normal"), ("Mod+Alt+1", "para.heading1"),
        ("Mod+Alt+2", "para.heading2"), ("Mod+Alt+3", "para.heading3"),
        ("Mod+Shift+L", "para.bullets"), ("Mod+Shift+F", "format.font"),
        ("Mod+Shift+P", "format.size"), ("Mod+]", "format.growFont1"),
        ("Mod+[", "format.shrinkFont1"), ("Mod+Left", "caret.wordLeft"),
        ("Mod+Right", "caret.wordRight"), ("Mod+Home", "caret.docStart"),
        ("Mod+End", "caret.docEnd"), ("Mod+F", "edit.find"),
        ("Mod+G", "edit.findNext"), ("Mod+H", "edit.findReplace"),
        ("Mod+Alt+G", "edit.goto"), ("F5", "edit.goto"), ("Tab", "text.tab"),
        ("Shift+Tab", "text.backTab"), ("Mod+Tab", "text.insertTab"),
        ("Mod+K", "insert.link"), ("Mod+Alt+M", "review.newComment"),
        ("Mod+Shift+E", "review.trackChanges"), ("Alt+Shift+D", "insert.dateField"),
        ("Alt+Shift+T", "insert.timeField"),
    ];
    for (chord, expected_command) in bindings {
        let actual = keymap.resolve(&registry, chord).map(|command| command.id);
        assert_eq!(actual, Some(expected_command), "shortcut {chord} must resolve to {expected_command}");
    }
}

#[test]
fn word_style_conflicts_repeat_extend_selection_and_unbound_function_keys_are_explicit() {
    let registry = cmd::registry();
    let keymap = KeyMap::default();
    assert_eq!(keymap.resolve(&registry, "Mod+G").map(|s| s.id), Some("edit.findNext"));
    assert_eq!(keymap.resolve(&registry, "Mod+Alt+G").map(|s| s.id), Some("edit.goto"));
    assert_eq!(keymap.resolve(&registry, "Mod+Shift+S").map(|s| s.id), Some("styles.apply"));
    assert_eq!(keymap.resolve(&registry, "F12").map(|s| s.id), Some("file.saveAs"));
    assert_eq!(keymap.resolve(&registry, "Mod+Shift+V").map(|s| s.id), Some("edit.pasteFormat"));
    assert_eq!(keymap.resolve(&registry, "Mod+Alt+V").map(|s| s.id), Some("edit.pasteSpecial"));
    assert_eq!(keymap.resolve(&registry, "Mod+Shift+Alt+V").map(|s| s.id), Some("edit.pasteText"));
    assert_eq!(keymap.resolve(&registry, "F4").map(|s| s.id), Some("edit.repeat"));
    assert_eq!(keymap.resolve(&registry, "F8").map(|s| s.id), Some("select.extend"));
    for chord in ["F6", "F10", "F11"] {
        assert_eq!(keymap.resolve(&registry, chord).map(|s| s.id), None, "{chord} is not implemented in the pinned registry");
    }
}
