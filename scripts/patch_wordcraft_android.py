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

    # Android's InputConnection can report one physical key through both the IME bridge
    # (commit/delete/editor action) and GameActivity's native key queue. Route handled
    # editing keys through exactly one path, while leaving navigation/modifier keys native.
    activity = builder / "templates/android/SafActivity.java"
    replace_once(
        activity,
        """                            imeKeySynthesized.add(event.getKeyCode());
                            return super.sendKeyEvent(event);""",
        """                            boolean physicalKeyboardEvent =
                                    event.getDeviceId() != android.view.KeyCharacterMap.VIRTUAL_KEYBOARD
                                    && event.isFromSource(android.view.InputDevice.SOURCE_KEYBOARD);
                            if (physicalKeyboardEvent) {
                                // Hardware keys belong to WordCraft's native key dispatcher.
                                // Do not translate Backspace/Delete into IME DeleteSurrounding:
                                // that IME operation intentionally does not join paragraph marks.
                                // Forward the event to the host view; its onKeyDown/onKeyUp lets
                                // physical keys fall through to GameActivity and winit.
                                return super.sendKeyEvent(event);
                            }
                            // Only virtual-IME synthesized keys are represented by queued IME
                            // events. Consume their forwarded Android key pair to avoid duplicates.
                            imeKeySynthesized.add(event.getKeyCode());
                            return super.sendKeyEvent(event);""",
        "deduplicate physical editing keys forwarded through Android IME",
    )
    replace_once(
        activity,
        """    private final java.util.Set<Integer> imeKeySynthesized = java.util.Collections.synchronizedSet(new java.util.HashSet<>());""",
        """    private final java.util.Set<Integer> imeKeySynthesized = java.util.Collections.synchronizedSet(new java.util.HashSet<>());
    // Space and Enter may each arrive through two different InputConnection callbacks for one
    // physical press. Suppress only cross-callback pairs; repeated calls from the same source
    // remain valid key repeats / deliberate rapid taps.
    private static final long IME_TEXT_PAIR_MS = 50L;
    private volatile long lastImeSpaceCommitAt = 0L;
    private volatile long lastImeSpaceKeyAt = 0L;
    private volatile long lastImeEnterActionAt = 0L;
    private volatile long lastImeEnterKeyAt = 0L;""",
        "Android IME cross-callback deduplication state",
    )
    replace_once(
        activity,
        """                            if (text != null && text.length() > 0) {
                                queueImeEvent("c" + text);
                            }""",
        """                            if (text != null && text.length() > 0) {
                                if (!" ".contentEquals(text) || claimImeSpace("commit")) {
                                    queueImeEvent("c" + text);
                                }
                            }""",
        "deduplicate IME space commits",
    )
    replace_once(
        activity,
        """                                } else if (code == KeyEvent.KEYCODE_ENTER) {
                                    queueImeEvent("a6");
                                }""",
        """                                } else if (code == KeyEvent.KEYCODE_ENTER) {
                                    if (claimImeEnter("key")) {
                                        queueImeEvent("a6");
                                    }
                                } else if (code == KeyEvent.KEYCODE_SPACE
                                        && event.getDeviceId() != android.view.KeyCharacterMap.VIRTUAL_KEYBOARD
                                        && event.isFromSource(android.view.InputDevice.SOURCE_KEYBOARD)) {
                                    if (claimImeSpace("key")) {
                                        queueImeEvent("c ");
                                    }
                                }""",
        "deduplicate physical space and Enter key events",
    )
    replace_once(
        activity,
        """                        public boolean performEditorAction(int actionCode) {
                            queueImeEvent("a" + actionCode);
                            return super.performEditorAction(actionCode);
                        }""",
        """                        public boolean performEditorAction(int actionCode) {
                            if (actionCode != 0 && claimImeEnter("action")) {
                                queueImeEvent("a" + actionCode);
                            }
                            return super.performEditorAction(actionCode);
                        }""",
        "deduplicate Enter editor-action callbacks",
    )
    replace_once(
        activity,
        """    private boolean claimDelete(String method) {""",
        """    private boolean claimImeSpace(String method) {
        long now = android.os.SystemClock.uptimeMillis();
        long lastOther = "commit".equals(method) ? lastImeSpaceKeyAt : lastImeSpaceCommitAt;
        if (lastOther != 0L && now - lastOther < IME_TEXT_PAIR_MS) {
            if ("commit".equals(method)) lastImeSpaceKeyAt = 0L;
            else lastImeSpaceCommitAt = 0L;
            return false;
        }
        if ("commit".equals(method)) lastImeSpaceCommitAt = now;
        else lastImeSpaceKeyAt = now;
        return true;
    }

    private boolean claimImeEnter(String method) {
        long now = android.os.SystemClock.uptimeMillis();
        long lastOther = "action".equals(method) ? lastImeEnterKeyAt : lastImeEnterActionAt;
        if (lastOther != 0L && now - lastOther < IME_TEXT_PAIR_MS) {
            if ("action".equals(method)) lastImeEnterKeyAt = 0L;
            else lastImeEnterActionAt = 0L;
            return false;
        }
        if ("action".equals(method)) lastImeEnterActionAt = now;
        else lastImeEnterKeyAt = now;
        return true;
    }

    private boolean claimDelete(String method) {""",
        "Android IME cross-callback deduplication helpers",
    )

    # Coalesce Android IME wake-ups. A single key can produce commit/preedit/finish
    # callbacks, but the Rust bridge drains the entire queue in one frame. Waking the
    # GameActivity looper for every callback floods its native key queue and adds input lag.
    replace_once(
        activity,
        "import java.util.concurrent.TimeUnit;",
        "import java.util.concurrent.TimeUnit;\nimport java.util.concurrent.atomic.AtomicBoolean;",
        "IME wake coalescing import",
    )
    replace_once(
        activity,
        '    private final ConcurrentLinkedQueue<String> imeEvents = new ConcurrentLinkedQueue<>();',
        '    private final ConcurrentLinkedQueue<String> imeEvents = new ConcurrentLinkedQueue<>();\n    private final AtomicBoolean imeWakePending = new AtomicBoolean(false);',
        "IME wake coalescing state",
    )
    replace_once(
        activity,
        """    private void queueImeEvent(String event) {
        imeEvents.offer(event);
        try {
            super.onKeyDown(
                    KeyEvent.KEYCODE_UNKNOWN,
                    new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_UNKNOWN));
            super.onKeyUp(
                    KeyEvent.KEYCODE_UNKNOWN,
                    new KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_UNKNOWN));
        } catch (Throwable error) {
            Log.w(TAG, "Could not wake the native loop for a keyboard event", error);
        }
    }""",
        """    private void wakeImeLoop() {
        try {
            super.onKeyDown(
                    KeyEvent.KEYCODE_UNKNOWN,
                    new KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_UNKNOWN));
            super.onKeyUp(
                    KeyEvent.KEYCODE_UNKNOWN,
                    new KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_UNKNOWN));
        } catch (Throwable error) {
            Log.w(TAG, "Could not wake the native loop for a keyboard event", error);
        }
    }

    private void queueImeEvent(String event) {
        imeEvents.offer(event);
        if (imeWakePending.compareAndSet(false, true)) {
            wakeImeLoop();
        }
    }""",
        "coalesce Android IME native-loop wake-ups",
    )
    replace_once(
        activity,
        """    public String imePoll() {
        return imeEvents.poll();
    }""",
        """    public String imePoll() {
        String event = imeEvents.poll();
        if (event == null) {
            // Close the enqueue/poll race: if a producer added an event while the wake flag
            // was still set, arrange one fresh wake after clearing it.
            imeWakePending.set(false);
            if (!imeEvents.isEmpty() && imeWakePending.compareAndSet(false, true)) {
                wakeImeLoop();
            }
        }
        return event;
    }""",
        "race-safe IME wake reset",
    )

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

    # egui-winit's previous Android touch tracker cleared the first finger whenever a
    # second, distinct finger started, so the multi-touch branch could never be reached.
    # Track all active fingers and synthesize MouseWheel events from the two-finger centroid.
    egui_winit = builder / "vendor/egui-winit/src/lib.rs"
    replace_once(
        egui_winit,
        '''    gesture_touch_ids: Vec<u64>,
''',
        '''    gesture_touch_ids: Vec<u64>,
    /// Active Android touch positions for two-finger document scrolling.
    gesture_touch_positions: Vec<(u64, egui::Pos2)>,
    two_finger_scroll_last_centroid: Option<egui::Pos2>,
    two_finger_scroll_active: bool,
''',
        "Android two-finger scroll state",
    )
    replace_once(
        egui_winit,
        '''            gesture_touch_ids: Vec::new(),
''',
        '''            gesture_touch_ids: Vec::new(),
            gesture_touch_positions: Vec::new(),
            two_finger_scroll_last_centroid: None,
            two_finger_scroll_active: false,
''',
        "Android two-finger scroll initialization",
    )
    replace_once(
        egui_winit,
        '''        // Keep track of which fingers make up the current gesture. A finger we have not seen before
        // begins a fresh gesture, so the set resets to just that finger; a finger already in the
        // set is another finger of the gesture in progress and is added. Two or more means
        // multi-touch. A lifted finger is dropped, so a gesture that ends can never leave the set
        // (and the pointer suppression) stuck on. See \x60gesture_touch_ids\x60 for why both a reset on
        // \x60Started\x60 and a prune on \x60Ended\x60 are needed.
        match touch.phase {
            winit::event::TouchPhase::Started => {
                if !self.gesture_touch_ids.contains(&touch.id) {
                    self.gesture_touch_ids.clear();
                }
                self.gesture_touch_ids.push(touch.id);
            }
            winit::event::TouchPhase::Ended | winit::event::TouchPhase::Cancelled => {
                self.gesture_touch_ids.retain(|id| *id != touch.id);
            }
            winit::event::TouchPhase::Moved => {}
        }

        // Emit touch event
''',
        '''        // Keep the active finger set until each finger lifts. A new finger joins the
        // current gesture; it must not clear the first finger or multi-touch is never detected.
        let pos = egui::pos2(
            touch.location.x as f32 / pixels_per_point,
            touch.location.y as f32 / pixels_per_point,
        );
        match touch.phase {
            winit::event::TouchPhase::Started => {
                if !self.gesture_touch_ids.contains(&touch.id) {
                    self.gesture_touch_ids.push(touch.id);
                }
                if let Some((_, old_pos)) = self.gesture_touch_positions.iter_mut().find(|(id, _)| *id == touch.id) {
                    *old_pos = pos;
                } else {
                    self.gesture_touch_positions.push((touch.id, pos));
                }
            }
            winit::event::TouchPhase::Moved => {
                if let Some((_, old_pos)) = self.gesture_touch_positions.iter_mut().find(|(id, _)| *id == touch.id) {
                    *old_pos = pos;
                }
            }
            winit::event::TouchPhase::Ended | winit::event::TouchPhase::Cancelled => {
                self.gesture_touch_ids.retain(|id| *id != touch.id);
                self.gesture_touch_positions.retain(|(id, _)| *id != touch.id);
            }
        }

        // Emit touch event
''',
        "Android active touch tracking",
    )
    replace_once(
        egui_winit,
        '''            pos: egui::pos2(
                touch.location.x as f32 / pixels_per_point,
                touch.location.y as f32 / pixels_per_point,
            ),
''',
        '''            pos,
''',
        "Android touch position reuse",
    )
    replace_once(
        egui_winit,
        '''        });

        // A multi-finger gesture (two-finger scroll or pinch) must not also act on the pointer:
''',
        '''        });

        // Turn the movement of two active fingers into a normal egui scroll-wheel stream.
        // Use the centroid so both fingers contribute equally; the gesture never reaches the
        // document as a text-selection drag or an accidental pinch zoom.
        let active_positions = self
            .gesture_touch_ids
            .iter()
            .take(2)
            .filter_map(|id| self.gesture_touch_positions.iter().find(|(touch_id, _)| touch_id == id).map(|(_, p)| *p))
            .collect::<Vec<_>>();
        if active_positions.len() >= 2 {
            let centroid = (active_positions[0].to_vec2() + active_positions[1].to_vec2()) * 0.5;
            let centroid = egui::pos2(centroid.x, centroid.y);
            if !self.two_finger_scroll_active {
                self.two_finger_scroll_active = true;
                self.two_finger_scroll_last_centroid = Some(centroid);
                self.egui_input.events.push(egui::Event::MouseWheel {
                    unit: egui::MouseWheelUnit::Point,
                    delta: egui::Vec2::ZERO,
                    phase: egui::TouchPhase::Start,
                    modifiers: self.modifiers,
                });
            } else if let Some(previous) = self.two_finger_scroll_last_centroid {
                let delta = centroid - previous;
                if delta != egui::Vec2::ZERO {
                    self.egui_input.events.push(egui::Event::MouseWheel {
                        unit: egui::MouseWheelUnit::Point,
                        delta,
                        phase: egui::TouchPhase::Move,
                        modifiers: self.modifiers,
                    });
                }
                self.two_finger_scroll_last_centroid = Some(centroid);
            }
        } else if self.two_finger_scroll_active {
            self.two_finger_scroll_active = false;
            self.two_finger_scroll_last_centroid = None;
            self.egui_input.events.push(egui::Event::MouseWheel {
                unit: egui::MouseWheelUnit::Point,
                delta: egui::Vec2::ZERO,
                phase: egui::TouchPhase::End,
                modifiers: self.modifiers,
            });
            self.pointer_pos_in_points = None;
            self.egui_input.events.push(egui::Event::PointerGone);
        }

        // A multi-finger gesture (two-finger scroll or pinch) must not also act on the pointer:
''',
        "Android two-finger scroll wheel synthesis",
    )
    replace_once(
        egui_winit,
        '''            if self.pointer_touch_id.is_some() {
                self.pointer_touch_id = None;
                self.on_mouse_button_input(
                    winit::event::ElementState::Released,
                    winit::event::MouseButton::Left,
                );
            }
''',
        '''            if let Some(pointer_id) = self.pointer_touch_id.take() {
                let pointer_pos = self
                    .gesture_touch_positions
                    .iter()
                    .find(|(id, _)| *id == pointer_id)
                    .map(|(_, p)| *p)
                    .unwrap_or(pos);
                self.egui_input.events.push(egui::Event::Touch {
                    device_id: egui::TouchDeviceId(egui::epaint::util::hash(touch.device_id)),
                    id: egui::TouchId::from(pointer_id),
                    phase: egui::TouchPhase::Cancel,
                    pos: pointer_pos,
                    force: None,
                });
                self.on_mouse_button_input(
                    winit::event::ElementState::Released,
                    winit::event::MouseButton::Left,
                );
            }
''',
        "cancel single-finger selection when two-finger scroll begins",
    )

    replace_once(
        egui_winit,
        '''            if self.pointer_pos_in_points.is_some() {
                self.pointer_pos_in_points = None;
                self.egui_input.events.push(egui::Event::PointerGone);
            }
''',
        '''            if let Some(centroid) = self.two_finger_scroll_last_centroid {
                self.pointer_pos_in_points = Some(centroid);
                self.egui_input.events.push(egui::Event::PointerMoved(centroid));
            }
''',
        "keep the scroll hit target under the two-finger centroid",
    )
    # The generated launcher is kept in the source checkout. Bump its marker whenever its
    # generated Rust changes, so a reused checkout cannot keep an older incompatible wrapper.
    replace_once(
        common,
        'GENERATOR_VERSION = "61"',
        'GENERATOR_VERSION = "64"',
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

    # The new Android IME-hide field is app-wide, so swap_window must explicitly
    # leave it on the active WordApp rather than destructuring an incomplete pattern.
    window_ui = source / "crates/ui-egui/src/window_ui.rs"
    replace_once(
        window_ui,
        "            shown_document,\n        } = self;",
        "            shown_document,\n            request_ime_hide: _,\n        } = self;",
        "WordApp window-swap IME field",
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
        activity,
        (
            "boolean physicalKeyboardEvent =",
            "if (physicalKeyboardEvent)",
            "Hardware keys belong to WordCraft's native key dispatcher.",
            "imeKeySynthesized.add(event.getKeyCode());",
            'claimImeSpace("commit")',
            'claimImeEnter("action")',
            "event.getKeyCode() == KeyEvent.KEYCODE_SPACE",
            "imeWakePending.compareAndSet(false, true)",
            "private void wakeImeLoop()",
        ),
        "Android physical editing-key deduplication",
    )
    require(
        egui_winit,
        (
            "gesture_touch_positions: Vec<(u64, egui::Pos2)>",
            "two_finger_scroll_last_centroid: Option<egui::Pos2>",
            "self.two_finger_scroll_active = true;",
            "egui::Event::MouseWheel",
            "egui::TouchPhase::Cancel",
        ),
        "Android two-finger touch scrolling",
    )
    require(
        common,
        (
            "modifiers.shift || modifiers.alt",
            'GENERATOR_VERSION = "64"',
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
        window_ui,
        ("request_ime_hide: _,",),
        "WordApp window-swap IME field",
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
