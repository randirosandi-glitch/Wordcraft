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

    activity = builder / "templates/android/SafActivity.java"

    # The Android shell must not synthesize ordinary clipboard events for
    # Ctrl+Shift+C/V: WordCraft already binds those exact chords to Copy/Paste Formatting.
    replace_once(
        common,
        '''            if !modifiers.command && !modifiers.ctrl {{
                continue;
            }}''',
        '''            if (!modifiers.command && !modifiers.ctrl) || modifiers.shift || modifiers.alt {{
                continue;
            }}''',
        "preserve WordCraft formatting clipboard shortcuts",
    )

    # Two-finger touch, trackpad scroll, gesture takeover and Android momentum are handled
    # by ArtCraft's current vendored Winit backend and lib/scrolling.sh. Do not duplicate them here.

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

    # ArtCraft's lib/scrolling.sh adds the WordApp/canvas IME-hide state and gesture guards.
    # Its build-common hook applies those changes to this pinned source checkout.

    # SAF results are produced by Android activity callbacks and background URI-copy workers.
    # The native loop may be idle after the picker returns; queueing alone does not request a
    # frame, so the user had to tap the screen before the selected document appeared. Wake the
    # GameActivity loop on the UI thread whenever a picker result or incoming file is queued.
    replace_once(
        activity,
        "    public String safPoll() { return results.poll(); }",
        """    private void enqueueSafResult(String value) {
        results.offer(value);
        wakeNativeLoop();
    }

    private void enqueueIntentPath(String value) {
        intentPaths.offer(value);
        wakeNativeLoop();
    }

    public String safPoll() { return results.poll(); }""",
        "wake native loop when Android SAF results arrive",
    )
    activity_text = activity.read_text(encoding="utf-8")
    activity_text = activity_text.replace("results.offer(", "enqueueSafResult(")
    activity_text = activity_text.replace("intentPaths.offer(", "enqueueIntentPath(")
    activity_text = activity_text.replace(
        "private void enqueueSafResult(String value) {\n        enqueueSafResult(value);",
        "private void enqueueSafResult(String value) {\n        results.offer(value);",
    )
    activity_text = activity_text.replace(
        "private void enqueueIntentPath(String value) {\n        enqueueIntentPath(value);",
        "private void enqueueIntentPath(String value) {\n        intentPaths.offer(value);",
    )
    activity.write_text(activity_text, encoding="utf-8")

    require(
        activity,
        (
            "private static boolean isFromSoftKeyboard(KeyEvent event)",
            "private final class ObservableEditable extends SpannableStringBuilder",
            "public Editable getEditable()",
            "private void wakeNativeLoop()",
            "private void enqueueSafResult(String value)",
            "private void enqueueIntentPath(String value)",
            "wakeNativeLoop();",
        ),
        "Upstream Android IME and WordCraft SAF wake integration",
    )
    require(
        common,
        (
            "modifiers.shift || modifiers.alt",
            'GENERATOR_VERSION = "71"',
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
    scrolling = builder / "lib/scrolling.sh"
    android_winit = builder / "vendor/winit/src/platform_impl/android/mod.rs"
    require(
        scrolling,
        (
            "pub request_ime_hide: bool",
            "pub surrendered_focus: bool",
            "fn touch_gesture_active(ui: &Ui) -> bool",
            "app.canvas.cancel_text_drag();",
            "SYNTH_MOMENTUM",
        ),
        "Upstream WordCraft gesture and IME-hide patch",
    )
    require(
        android_winit,
        (
            "fn recognise_touch_gesture(",
            "GestureStep::Pan(delta)",
            "update_modifiers(key.meta_state(), callback);",
            "android_app.enable_motion_axis(Axis::Vscroll);",
        ),
        "Upstream Android Winit gesture and keyboard support",
    )
    require(
        common,
        (
            'bash "$ROOT/lib/scrolling.sh" "$SRC" "$APP" "$TITLE"',
            "reset_ime_with_request",
        ),
        "ArtCraft source integration",
    )
    require(
        source / "vendor/winit/src/window.rs",
        ("reset_ime_with_request",),
        "WordCraft Winit IME reset API",
    )
    require(
        source / "vendor/winit/src/event.rs",
        ("ImeResetCompleted",),
        "WordCraft Winit IME reset event",
    )

    print(
        "Applied and verified WordCraft Android compatibility patches "
        f"against {WORDCRAFT_COMMIT}."
    )


if __name__ == "__main__":
    main()
