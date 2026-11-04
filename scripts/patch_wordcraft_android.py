#!/usr/bin/env python3
"""Apply audited Android compatibility patches to the pinned WordCraft v0.15.0 source."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORDCRAFT_COMMIT = "b47079fc791595fd84bb499d64dcd3f0624ef35a"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{label}: expected exactly one source anchor in {path}, found {count}; "
            "refusing a speculative patch"
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def require(path: Path, needles: tuple[str, ...], label: str) -> None:
    text = path.read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f"{label}: post-patch verification failed in {path}: {missing!r}")


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: patch_wordcraft_android.py ARTCRAFT_ROOT WORDCRAFT_SOURCE")

    builder = Path(sys.argv[1]).resolve()
    source = Path(sys.argv[2]).resolve()
    if not (builder / "lib/build-common.sh").is_file():
        raise SystemExit(f"Not an ArtCraft checkout: {builder}")
    if not (source / ".git").is_dir():
        raise SystemExit(f"Not a Git checkout: {source}")

    commit = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != WORDCRAFT_COMMIT:
        raise SystemExit(
            f"Unexpected WordCraft source commit {commit}; expected {WORDCRAFT_COMMIT}"
        )

    cargo_lock = (source / "Cargo.lock").read_text(encoding="utf-8")
    for dependency_pin in (
        "6d518fc799681571963842f95b55a6b68431b15a",
        "a517b3846ee8457d84ee4975110bfda6797c44dc",
        'name = "egui-winit"\nversion = "0.37.0"',
    ):
        if dependency_pin not in cargo_lock:
            raise SystemExit(f"WordCraft Cargo.lock is missing expected dependency pin: {dependency_pin}")

    common = builder / "lib/build-common.sh"

    # The generated launcher is kept in the source checkout. Bump its marker whenever its
    # generated Rust changes, so a reused checkout cannot keep an older incompatible wrapper.
    replace_once(
        common,
        'GENERATOR_VERSION = "61"',
        'GENERATOR_VERSION = "62"',
        "launcher generator version",
    )

    # WordCraft's current API requires both Context and RawInput. Other ArtCraft apps retain
    # their existing one-argument hook contract.
    replace_once(
        common,
        '''        if has_raw_hook:
            inner_hook = "let _ = ctx;\\n        self.inner.raw_input_hook(raw);"''',
        '''        if has_raw_hook:
            if app == "wordcraft":
                inner_hook = "self.inner.raw_input_hook(ctx, raw);"
            else:
                inner_hook = "let _ = ctx;\\n        self.inner.raw_input_hook(raw);"''',
        "WordCraft raw_input_hook adapter",
    )

    # WordCraft's Printer API has a label field; omitting it caused E0063.
    replace_once(
        common,
        '''            let _ = tx.send(vec![wordcraft_ui_egui::printing::Printer {
                name: "Android print system".to_owned(),
                default: true,
            }]);''',
        '''            let _ = tx.send(vec![wordcraft_ui_egui::printing::Printer {
                name: "Android print system".to_owned(),
                label: "Android print system".to_owned(),
                default: true,
            }]);''',
        "WordCraft Android printer",
    )

    # The 0.37 egui-winit Git dependency uses its in-app fallback clipboard on Android.
    # Forward CopyText to Android ClipboardManager, and inject a SAF bridge callback for
    # WordCraft's ribbon/context-menu Paste commands.
    replace_once(
        common,
        '''        {inner_ui}
        if self.back_pending {{''',
        '''        {inner_ui}
        let clipboard_copies = ui.ctx().output(|output| {{
            output.commands.iter().filter_map(|command| match command {{
                egui::OutputCommand::CopyText(text) => Some(text.clone()),
                _ => None,
            }}).collect::<Vec<_>>()
        }});
        for text in clipboard_copies {{
            android_clipboard_set(&self.app, &text);
        }}
        if self.back_pending {{''',
        "Android system clipboard output bridge",
    )

    # Patch only the WordCraft SAF recipe, not the other ArtCraft app recipes.
    text = common.read_text(encoding="utf-8")
    saf_start = text.index("SAF_RECIPES = {")
    wordcraft_start = text.index('    "wordcraft": {', saf_start)
    persist_start = text.index("\nPERSIST_RECIPES = {", wordcraft_start)
    wordcraft_block = text[wordcraft_start:persist_start]
    services_start = wordcraft_block.index('        "services": \'\'\'')
    poll_start = wordcraft_block.index('        "poll":', services_start)
    services_block = wordcraft_block[services_start:poll_start]

    old_bridge_lines = '''    let print_bridge = bridge.clone_ref();
    let dialog_bridge = bridge.clone_ref();'''
    new_bridge_lines = '''    let print_bridge = bridge.clone_ref();
    let clipboard_bridge = bridge.clone_ref();
    let dialog_bridge = bridge.clone_ref();'''
    if new_bridge_lines not in services_block:
        if services_block.count(old_bridge_lines) != 1:
            raise SystemExit("WordCraft SAF clipboard bridge: expected one bridge declaration anchor")
        services_block = services_block.replace(old_bridge_lines, new_bridge_lines, 1)

    old_inbox = '''        inbox: Some(inbox),
        ..Services::default()'''
    new_inbox = '''        clipboard_text: Some(Box::new(move || clipboard_bridge.clipboard_text())),
        inbox: Some(inbox),
        ..Services::default()'''
    if new_inbox not in services_block:
        if services_block.count(old_inbox) != 1:
            raise SystemExit("WordCraft SAF clipboard service: expected one Services initializer anchor")
        services_block = services_block.replace(old_inbox, new_inbox, 1)

    wordcraft_block = (
        wordcraft_block[:services_start]
        + services_block
        + wordcraft_block[poll_start:]
    )
    text = text[:wordcraft_start] + wordcraft_block + text[persist_start:]
    common.write_text(text, encoding="utf-8")

    # The generator's existing android_clipboard_get helper is the single JNI read path.
    # Expose it through the SAF Bridge so WordCraft's normal Services::clipboard_text hook
    # works for ribbon and context-menu Paste, not only Ctrl+V.
    saf_bridge = builder / "templates/android/saf_bridge.rs"
    replace_once(
        saf_bridge,
        '''        pub fn clone_ref(&self) -> Self {
            Self {
                app: self.app.clone(),
                vm: Arc::clone(&self.vm),
            }
        }
''',
        '''        pub fn clone_ref(&self) -> Self {
            Self {
                app: self.app.clone(),
                vm: Arc::clone(&self.vm),
            }
        }

        /// Read plain text from Android ClipboardManager for the app's normal Paste services.
        pub fn clipboard_text(&self) -> Option<String> {
            let text = super::android_clipboard_get(&self.app);
            (!text.is_empty()).then_some(text)
        }
''',
        "SAF clipboard read bridge",
    )

    # WordApp owns the one-frame request consumed by the Android shell's logic tick.
    wordapp_lib = source / "crates/ui-egui/src/lib.rs"
    replace_once(
        wordapp_lib,
        "    pub(crate) comment_drafts: panes::CommentDrafts,\n",
        "    pub(crate) comment_drafts: panes::CommentDrafts,\n"
        "    /// Android: the canvas surrendered focus to a scroll/draw gesture; the host hides IME.\n"
        "    pub request_ime_hide: bool,\n",
        "WordApp IME-hide state",
    )

    wordapp_app = source / "crates/ui-egui/src/app.rs"
    replace_once(
        wordapp_app,
        "            comment_drafts: Default::default(),\n",
        "            comment_drafts: Default::default(),\n"
        "            request_ime_hide: false,\n",
        "WordApp IME-hide initialization",
    )

    canvas = source / "crates/ui-egui/src/canvas.rs"

    # Track a one-frame focus surrender separately from ordinary text-selection drags.
    replace_once(
        canvas,
        "    pub want_focus: bool,\n",
        "    pub want_focus: bool,\n"
        "    pub(crate) surrendered_focus: bool,\n",
        "canvas focus-surrender state",
    )
    replace_once(
        canvas,
        "            want_focus: true,\n",
        "            want_focus: true,\n"
        "            surrendered_focus: false,\n",
        "canvas focus-surrender initialization",
    )
    replace_once(
        canvas,
        "    let full = ui.available_rect_before_wrap();\n",
        "    let full = ui.available_rect_before_wrap();\n"
        "    app.canvas.surrendered_focus = false;\n",
        "canvas focus-surrender frame reset",
    )

    # In v0.15.0 the canvas response is factored into canvas_response(); the older ArtCraft
    # scrolling patch targeted an inline ui.interact call that no longer exists.
    replace_once(
        canvas,
        "fn canvas_response(ui: &mut Ui, content: Rect, scroll_target: Option<Rect>) -> egui::Response {\n",
        "fn canvas_response(app: &mut WordApp, ui: &mut Ui, content: Rect, scroll_target: Option<Rect>) -> egui::Response {\n",
        "canvas response adapter signature",
    )
    replace_once(
        canvas,
        '    let response = ui.interact(content, egui::Id::unique("wordcraft_canvas"), Sense::click_and_drag());\n',
        '''    let response = ui.interact(content, egui::Id::unique("wordcraft_canvas"), Sense::click_and_drag());
    if cfg!(target_os = "android") {
        let is_scrolling = app.canvas.auto_scroll.blocks_input();
        let is_drawing = app.canvas.ink.is_some()
            || app.session.view.draw.mode != wordcraft_engine::cmd::draw::DrawMode::Select
            || app.canvas.table_tool.is_some();
        let is_object_drag = app.canvas.obj_drag.is_some() || app.canvas.crop_drag.is_some();
        let touch_gesture = ui.input(|i| {
            i.events.iter().any(|event| {
                matches!(event, egui::Event::Touch { phase: egui::TouchPhase::Cancel, .. })
            })
        });
        let is_text_drag = response.drag_started()
            && !is_scrolling
            && !is_drawing
            && !is_object_drag
            && !ui.input(|i| i.pointer.button_down(egui::PointerButton::Middle));
        if touch_gesture || ((is_scrolling || is_drawing || is_object_drag) && !is_text_drag) {
            response.surrender_focus();
            app.canvas.surrendered_focus = true;
            app.request_ime_hide = true;
        }
    }
''',
        "canvas Android gesture/IME handling",
    )
    replace_once(
        canvas,
        "        let resp = canvas_response(ui, content, scroll_target);\n",
        "        let resp = canvas_response(app, ui, content, scroll_target);\n",
        "canvas response call",
    )

    # A surrendered canvas must not immediately reacquire focus or ask egui to reopen IME.
    replace_once(
        canvas,
        "    let focus_click = pointer_click || accesskit_click || resp.drag_started();\n",
        "    let focus_click = !app.canvas.surrendered_focus && (pointer_click || accesskit_click || resp.drag_started());\n",
        "canvas gesture focus guard",
    )
    replace_once(
        canvas,
        "    if focus_click || (app.canvas.want_focus && !resp.has_focus()) {\n",
        "    let want_focus_honored = if cfg!(target_os = \"android\") { false } else { app.canvas.want_focus };\n"
        "    if focus_click || (want_focus_honored && !resp.has_focus()) {\n",
        "Android initial-focus behavior",
    )
    replace_once(
        canvas,
        "    crate::keys::observe_ime(app, ui.ctx(), ime_geometry, ime_interrupt);\n",
        "    if !app.canvas.surrendered_focus {\n"
        "        crate::keys::observe_ime(app, ui.ctx(), ime_geometry, ime_interrupt);\n"
        "    }\n",
        "canvas IME observation guard",
    )

    require(
        common,
        (
            'GENERATOR_VERSION = "62"',
            "self.inner.raw_input_hook(ctx, raw);",
            'label: "Android print system".to_owned(),',
            "android_clipboard_set(&self.app, &text);",
            "clipboard_bridge.clipboard_text()",
        ),
        "ArtCraft generator",
    )
    require(
        saf_bridge,
        ("pub fn clipboard_text(&self) -> Option<String>", "super::android_clipboard_get(&self.app)"),
        "SAF clipboard bridge",
    )
    require(
        wordapp_lib,
        ("pub request_ime_hide: bool",),
        "WordApp IME state",
    )
    require(
        wordapp_app,
        ("request_ime_hide: false,",),
        "WordApp IME initialization",
    )
    require(
        canvas,
        (
            "pub(crate) surrendered_focus: bool",
            "surrendered_focus: false,",
            "response.surrender_focus();",
            "app.request_ime_hide = true;",
            "canvas_response(app, ui, content, scroll_target)",
            "if !app.canvas.surrendered_focus",
        ),
        "WordCraft canvas IME integration",
    )

    print(
        "Applied and verified WordCraft Android compatibility patches "
        f"against {WORDCRAFT_COMMIT}."
    )


if __name__ == "__main__":
    main()
