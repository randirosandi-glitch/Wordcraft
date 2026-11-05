#!/usr/bin/env python3
"""Apply audited Android compatibility patches to the pinned WordCraft v0.15.0 source."""

from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
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


def integrate_android_icon_pack(builder: Path, source: Path) -> None:
    """Install the user-supplied, pre-rendered Android icon resources into ArtCraft's generator."""
    archive = builder.parent / "workspace" / "assets" / "android-icon-pack" / "wc.zip"
    if not archive.is_file():
        raise SystemExit(f"Required Android icon archive is missing: {archive}")

    destination = source / "assets" / "android-icon-pack"
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise SystemExit(f"Unsafe path in Android icon archive: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(member) as src_file, target.open("wb") as dst_file:
                    shutil.copyfileobj(src_file, dst_file)

    resource_root = destination / "android" / "app" / "src" / "main" / "res"
    required = (
        resource_root / "mipmap-mdpi" / "ic_launcher.png",
        resource_root / "mipmap-xxxhdpi" / "ic_launcher.png",
        resource_root / "mipmap-anydpi-v26" / "ic_launcher.xml",
        resource_root / "mipmap-anydpi-v26" / "ic_launcher_round.xml",
        resource_root / "drawable" / "ic_launcher_monochrome.png",
        resource_root / "values" / "colors.xml",
        destination / "play-store-icon-512.png",
    )
    missing = [str(path.relative_to(destination)) for path in required if not path.is_file()]
    if missing:
        raise SystemExit(f"Android icon archive is incomplete; missing: {missing}")

    # Android 13+ themed icons need an explicit monochrome layer. The supplied archive
    # includes the glyph PNG; wire it into both adaptive-icon definitions.
    for xml_name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        xml = resource_root / "mipmap-anydpi-v26" / xml_name
        content = xml.read_text(encoding="utf-8")
        if "<monochrome " not in content:
            content = content.replace(
                "</adaptive-icon>",
                '    <monochrome android:drawable="@drawable/ic_launcher_monochrome" />\n</adaptive-icon>',
            )
            xml.write_text(content, encoding="utf-8")

    # ArtCraft normally regenerates icons from a single raster/vector. For WordCraft,
    # preserve the supplied, density-specific resources byte-for-byte instead.
    generator = builder / "lib" / "app_icons.py"
    generator_text = generator.read_text(encoding="utf-8")
    newline = chr(10)
    import_anchor = "import sys" + newline + "from pathlib import Path"
    import_replacement = "import shutil" + newline + import_anchor
    if import_replacement not in generator_text:
        if generator_text.count(import_anchor) != 1:
            raise SystemExit("Android icon generator: import anchor was not unique")
        generator_text = generator_text.replace(import_anchor, import_replacement, 1)
        generator.write_text(generator_text, encoding="utf-8")
    old = "    Image, _ = _pillow()\n    source = pick_source(src, app, explicit)"
    new = '''    supplied = src / "assets" / "android-icon-pack" / "android" / "app" / "src" / "main" / "res"
    if supplied.is_dir():
        res_dir.mkdir(parents=True, exist_ok=True)
        for item in supplied.iterdir():
            target = res_dir / item.name
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
        return src / "assets" / "android-icon-pack" / "play-store-icon-512.png"

    Image, _ = _pillow()
    source = pick_source(src, app, explicit)'''
    text = generator.read_text(encoding="utf-8")
    if new not in text:
        if text.count(old) != 1:
            raise SystemExit("Android icon generator: expected exactly one generate() insertion point")
        generator.write_text(text.replace(old, new, 1), encoding="utf-8")

    # Expose the round adaptive resource to Android launchers that query roundIcon.
    common = builder / "lib" / "build-common.sh"
    common_text = common.read_text(encoding="utf-8")
    old_icon = 'icon = "@mipmap/ic_launcher"'
    new_icon = old_icon + '\nround_icon = "@mipmap/ic_launcher_round"'
    if new_icon not in common_text:
        if common_text.count(old_icon) != 1:
            raise SystemExit("Android roundIcon: expected exactly one launcher metadata anchor")
        common.write_text(common_text.replace(old_icon, new_icon, 1), encoding="utf-8")

    android_project = builder / "lib" / "android_project.py"
    project_text = android_project.read_text(encoding="utf-8")
    old_attrs = '(("label", "android:label"), ("theme", "android:theme"), ("icon", "android:icon"))'
    new_attrs = '(("label", "android:label"), ("theme", "android:theme"), ("icon", "android:icon"), ("round_icon", "android:roundIcon"))'
    if new_attrs not in project_text:
        if project_text.count(old_attrs) != 1:
            raise SystemExit("Android roundIcon manifest: expected exactly one attribute list")
        android_project.write_text(project_text.replace(old_attrs, new_attrs, 1), encoding="utf-8")

    print("Integrated supplied Android launcher resources (all densities, adaptive, round, monochrome).")


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
        """                            if (physicalKeyboardEvent) {
                                if (event.getAction() == KeyEvent.ACTION_DOWN) {
                                    int code = event.getKeyCode();
                                    boolean handledByImeCallback = false;
                                    // Some hardware keyboards are delivered both as a native
                                    // GameActivity key and as an InputConnection echo. Whichever
                                    // representation arrives first owns the edit; suppress only
                                    // the second path. The claim helpers also arbitrate against
                                    // paired IME callbacks (deleteSurroundingText, commitText,
                                    // performEditorAction) regardless of callback order.
                                    if (code == KeyEvent.KEYCODE_DEL
                                            || code == KeyEvent.KEYCODE_FORWARD_DEL) {
                                        handledByImeCallback = !claimDelete("s");
                                    } else if (code == KeyEvent.KEYCODE_ENTER) {
                                        handledByImeCallback = !claimImeEnter("key");
                                    } else if (code == KeyEvent.KEYCODE_SPACE) {
                                        handledByImeCallback = !claimImeSpace("key");
                                    }
                                    if (handledByImeCallback) {
                                        // The paired IME callback already produced the edit.
                                        // Consume this forwarded KeyEvent so it cannot apply twice.
                                        imeKeySynthesized.add(code);
                                    }
                                }
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
    private volatile long lastImeEnterKeyAt = 0L;
    // Physical-key and IME callbacks can represent the same press in either order.
    private static final long IME_NATIVE_PAIR_MS = 100L;
    private volatile int lastNativeEditKeyCode = KeyEvent.KEYCODE_UNKNOWN;
    private volatile long lastNativeEditAt = 0L;
    private volatile long lastNativeEditDownTime = 0L;
    private volatile int lastNativeEditDeviceId = -1;
    private volatile int lastImeEditKeyCode = KeyEvent.KEYCODE_UNKNOWN;
    private volatile long lastImeEditAt = 0L;""",
        "Android IME cross-callback deduplication state",
    )
    replace_once(
        activity,
        """                            if (text != null && text.length() > 0) {
                                queueImeEvent("c" + text);
                            }""",
        """                            if (text != null && text.length() > 0) {
                                if (!" ".contentEquals(text)) {
                                    queueImeEvent("c" + text);
                                } else if (shouldQueueImeEdit(KeyEvent.KEYCODE_SPACE)
                                        && claimImeSpace("commit")) {
                                    queueImeEvent("c" + text);
                                    noteImeEdit(KeyEvent.KEYCODE_SPACE);
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
                                }""",
        "deduplicate Enter IME key/editor-action callbacks",
    )
    # Determine whether the event is from a physical keyboard *before* sending it
    # through the IME edit bridge. Physical keys must reach winit once; virtual IME
    # keys must become queued IME operations and have their forwarded key pair consumed.
    replace_once(
        activity,
        """                            if (event.getAction() == KeyEvent.ACTION_DOWN) {
                                int code = event.getKeyCode();
                                if (code == KeyEvent.KEYCODE_DEL) {
                                    if (claimDelete("s")) {
                                        queueImeEvent("d1,0");
                                    }
                                } else if (code == KeyEvent.KEYCODE_FORWARD_DEL) {
                                    if (claimDelete("s")) {
                                        queueImeEvent("d0,1");
                                    }
                                } else if (code == KeyEvent.KEYCODE_ENTER) {
                                    if (claimImeEnter("key")) {
                                        queueImeEvent("a6");
                                    }
                                }
                            }""",
        """                            boolean physicalKeyboardEvent =
                                    event.getDeviceId() != android.view.KeyCharacterMap.VIRTUAL_KEYBOARD
                                    && event.isFromSource(android.view.InputDevice.SOURCE_KEYBOARD);
                            if (!physicalKeyboardEvent && event.getAction() == KeyEvent.ACTION_DOWN) {
                                int code = event.getKeyCode();
                                if (code == KeyEvent.KEYCODE_DEL) {
                                    if (claimDelete("s")) {
                                        queueImeEvent("d1,0");
                                    }
                                } else if (code == KeyEvent.KEYCODE_FORWARD_DEL) {
                                    if (claimDelete("s")) {
                                        queueImeEvent("d0,1");
                                    }
                                } else if (code == KeyEvent.KEYCODE_ENTER) {
                                    if (claimImeEnter("key")) {
                                        queueImeEvent("a6");
                                    }
                                }
                            }""",
        "separate physical keyboard keys from virtual IME operations",
    )
    replace_once(
        activity,
        """                        public boolean deleteSurroundingText(int beforeLength, int afterLength) {
                            if (beforeLength > 0 || afterLength > 0) {
                                if (claimDelete("d")) {
                                    queueImeEvent("d" + beforeLength + "," + afterLength);
                                }
                            }
                            return super.deleteSurroundingText(beforeLength, afterLength);
                        }""",
        """                        public boolean deleteSurroundingText(int beforeLength, int afterLength) {
                            if (beforeLength > 0 || afterLength > 0) {
                                int keyCode = beforeLength > 0
                                        ? KeyEvent.KEYCODE_DEL : KeyEvent.KEYCODE_FORWARD_DEL;
                                if (shouldQueueImeEdit(keyCode) && claimDelete("d")) {
                                    queueImeEvent("d" + beforeLength + "," + afterLength);
                                    noteImeEdit(keyCode);
                                }
                            }
                            return super.deleteSurroundingText(beforeLength, afterLength);
                        }""",
        "deduplicate native and IME delete callbacks",
    )
    replace_once(
        activity,
        """                        public boolean performEditorAction(int actionCode) {
                            queueImeEvent("a" + actionCode);
                            return super.performEditorAction(actionCode);
                        }""",
        """                        public boolean performEditorAction(int actionCode) {
                            if (actionCode != 0 && shouldQueueImeEdit(KeyEvent.KEYCODE_ENTER)
                                    && claimImeEnter("action")) {
                                queueImeEvent("a" + actionCode);
                                noteImeEdit(KeyEvent.KEYCODE_ENTER);
                            }
                            return super.performEditorAction(actionCode);
                        }""",
        "deduplicate Enter editor-action callbacks",
    )
    replace_once(
        activity,
        """                public boolean onKeyDown(int keyCode, KeyEvent event) {
                    // A key the IME synthesised (see sendKeyEvent above): its deletion was already
                    // queued, so consuming it here stops it bubbling to the Activity and reaching
                    // winit as a second Backspace. Physical key events never carry the flag, so they
                    // still fall through to the native queue below and keep working.
                    if (imeKeySynthesized.contains(keyCode)) {
                        return true;
                    }
                    // Let hardware key events fall through to the native input queue (winit), exactly
                    // as they did before this view existed; the soft keyboard talks to us through the
                    // InputConnection instead. This keeps physical keyboards working.
                    return false;
                }""",
        """                public boolean onKeyDown(int keyCode, KeyEvent event) {
                    if (imeKeySynthesized.contains(keyCode)) {
                        return true;
                    }
                    boolean physicalKeyboardEvent =
                            event.getDeviceId() != android.view.KeyCharacterMap.VIRTUAL_KEYBOARD
                            && event.isFromSource(android.view.InputDevice.SOURCE_KEYBOARD);
                    boolean editKey = keyCode == KeyEvent.KEYCODE_DEL
                            || keyCode == KeyEvent.KEYCODE_FORWARD_DEL
                            || keyCode == KeyEvent.KEYCODE_ENTER
                            || keyCode == KeyEvent.KEYCODE_SPACE;
                    if (physicalKeyboardEvent && editKey) {
                        // The native event owns the edit if it arrives first. If an IME callback
                        // already queued this same press, consume this copy instead.
                        return !allowNativeEditKey(event);
                    }
                    return false;
                }""",
        "deduplicate native and IME physical key dispatch",
    )
    replace_once(
        activity,
        """    private boolean claimDelete(String method) {""",
        """    private boolean shouldQueueImeEdit(int keyCode) {
        long now = android.os.SystemClock.uptimeMillis();
        return lastNativeEditKeyCode != keyCode || now - lastNativeEditAt >= IME_NATIVE_PAIR_MS;
    }

    private void noteImeEdit(int keyCode) {
        lastImeEditKeyCode = keyCode;
        lastImeEditAt = android.os.SystemClock.uptimeMillis();
    }

    private boolean allowNativeEditKey(KeyEvent event) {
        int keyCode = event.getKeyCode();
        long now = android.os.SystemClock.uptimeMillis();
        if (event.getRepeatCount() == 0) {
            if (lastImeEditKeyCode == keyCode && now - lastImeEditAt < IME_NATIVE_PAIR_MS) {
                return false;
            }
            if (lastNativeEditKeyCode == keyCode
                    && lastNativeEditDeviceId == event.getDeviceId()
                    && lastNativeEditDownTime == event.getDownTime()) {
                return false;
            }
        }
        lastNativeEditKeyCode = keyCode;
        lastNativeEditAt = now;
        lastNativeEditDownTime = event.getDownTime();
        lastNativeEditDeviceId = event.getDeviceId();
        return true;
    }

    private boolean claimImeSpace(String method) {
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

    # A background SAF mirror must not mark a provider write as saved before the
    # ContentResolver commit succeeds. Preserve the dirty stamp and retry with bounded
    # exponential backoff so a transient cloud-provider/network failure cannot lose a save.
    replace_once(
        saf_bridge,
        """        scanned: Option<Instant>,
""",
        """        scanned: Option<Instant>,
        /// A failed provider write stays dirty and is retried after this per-file deadline.
        retry_after: HashMap<String, Instant>,
        /// Bounded exponential backoff counter for each staged file.
        failures: HashMap<String, u8>,
""",
        "SAF save mirror retry state",
    )
    replace_once(
        saf_bridge,
        """    impl SaveMirror {
""",
        """    /// Keep failed provider commits dirty and retry with bounded exponential backoff.
    fn schedule_save_retry(tracked: &mut Tracked, candidate: &str, now: Instant) {
        let attempts = tracked.failures.entry(candidate.to_owned()).or_insert(0);
        *attempts = attempts.saturating_add(1);
        let exponent = u32::from((*attempts).saturating_sub(1).min(5));
        let seconds = (1_u64 << exponent).min(32);
        tracked.retry_after.insert(candidate.to_owned(), now + Duration::from_secs(seconds));
    }

    impl SaveMirror {
""",
        "SAF save retry scheduler",
    )
    replace_once(
        saf_bridge,
        """        /// Commit every tracked file whose contents changed since the last sync.
        pub fn sync(&self, bridge: &Bridge) {
            let mut entries = self.entries.lock().unwrap_or_else(|error| error.into_inner());
            for tracked in entries.values_mut() {
                if tracked.scanned.is_none_or(|at| at.elapsed() >= SCAN_INTERVAL) {
                    for candidate in family(&tracked.path) {
                        tracked.stamps.entry(candidate.clone()).or_insert_with(|| file_stamp(&candidate));
                    }
                    tracked.scanned = Some(Instant::now());
                }
                let candidates: Vec<String> = tracked.stamps.keys().cloned().collect();
                for candidate in candidates {
                    let stamp = file_stamp(&candidate);
                    if tracked.stamps.get(&candidate) == Some(&stamp) {
                        continue;
                    }
                    tracked.stamps.insert(candidate.clone(), stamp);
                    // An empty file is the staged copy the picker itself just created, not a write.
                    if stamp.1 == 0 {
                        continue;
                    }
                    match bridge.commit(&candidate) {
                        Ok(status) if status == "NONE" || status == "OK" => {}
                        Ok(status) => log::error!("Could not save {candidate}: {status}"),
                        Err(error) => log::error!("Could not save {candidate}: {error}"),
                    }
                }
            }
        }
""",
        """        /// Commit changed staged files. A provider failure does not advance the saved stamp:
        /// the local copy stays dirty and is retried after bounded backoff instead of being
        /// silently treated as synced. This also prevents a per-frame error-log storm when a
        /// cloud document provider is offline or temporarily refuses a write.
        pub fn sync(&self, bridge: &Bridge) {
            let mut entries = self.entries.lock().unwrap_or_else(|error| error.into_inner());
            for tracked in entries.values_mut() {
                if tracked.scanned.is_none_or(|at| at.elapsed() >= SCAN_INTERVAL) {
                    for candidate in family(&tracked.path) {
                        tracked.stamps.entry(candidate.clone()).or_insert_with(|| file_stamp(&candidate));
                    }
                    tracked.scanned = Some(Instant::now());
                }
                let candidates: Vec<String> = tracked.stamps.keys().cloned().collect();
                for candidate in candidates {
                    let stamp = file_stamp(&candidate);
                    if tracked.stamps.get(&candidate) == Some(&stamp) {
                        continue;
                    }
                    // An empty file is the staged copy the picker itself just created, not a write.
                    if stamp.1 == 0 {
                        tracked.stamps.insert(candidate.clone(), stamp);
                        continue;
                    }
                    let now = Instant::now();
                    if tracked.retry_after.get(&candidate).is_some_and(|retry_at| now < *retry_at) {
                        continue;
                    }
                    match bridge.commit(&candidate) {
                        Ok(status) if status == "NONE" || status == "OK" => {
                            tracked.stamps.insert(candidate.clone(), stamp);
                            tracked.retry_after.remove(&candidate);
                            tracked.failures.remove(&candidate);
                        }
                        Ok(status) => {
                            schedule_save_retry(tracked, &candidate, now);
                            log::warn!("Deferred SAF save for {candidate}; will retry: {status}");
                        }
                        Err(error) => {
                            schedule_save_retry(tracked, &candidate, now);
                            log::warn!("Deferred SAF save for {candidate}; will retry: {error}");
                        }
                    }
                }
            }
        }
""",
        "SAF save retry/backoff behavior",
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

    # A two-finger scroll cancels the first finger pointer touch in egui-winit.
    # Treat that cancellation as gesture takeover: stop an existing text-selection
    # drag and do not dispatch pointer editing while the gesture is active.
    replace_once(
        canvas,
        "fn handle_primary_pointer(\n",
        """fn touch_gesture_active(ui: &Ui) -> bool {
    ui.input(|i| {
        i.events.iter().any(|event| matches!(
            event,
            egui::Event::Touch { phase: egui::TouchPhase::Cancel, .. }
        ))
    })
}

fn handle_primary_pointer(
""",
        "WordCraft two-finger scroll gesture guard",
    )
    replace_once(
        canvas,
        """    if !middle_gesture && !crate::table_pen::pointer(app, ui, resp, rects, layout, geo.scale) {
        mouse(app, ui, resp, rects, layout, geo.scale);
    }""",
        """    if touch_gesture_active(ui) {
        // A second finger took over a drag that may already have started text selection.
        app.canvas.cancel_text_drag();
    } else if !middle_gesture && !crate::table_pen::pointer(app, ui, resp, rects, layout, geo.scale) {
        mouse(app, ui, resp, rects, layout, geo.scale);
    }""",
        "cancel text selection when two-finger scrolling takes over",
    )

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

    # SAF results are produced by Android activity callbacks and background URI-copy workers.
    # The native loop may be idle after the picker returns; queueing alone does not request a
    # frame, so the user had to tap the screen before the selected document appeared. Wake the
    # GameActivity loop on the UI thread whenever a picker result or incoming file is queued.
    replace_once(
        activity,
        "    public String safPoll() { return results.poll(); }",
        """    private void enqueueSafResult(String value) {
        results.offer(value);
        runOnUiThread(this::wakeImeLoop);
    }

    private void enqueueIntentPath(String value) {
        intentPaths.offer(value);
        runOnUiThread(this::wakeImeLoop);
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
            "boolean physicalKeyboardEvent =",
            "if (physicalKeyboardEvent)",
            "Some hardware keyboards are delivered both as a native",
            "imeKeySynthesized.add(code);",
            "shouldQueueImeEdit(KeyEvent.KEYCODE_ENTER)",
            "shouldQueueImeEdit(keyCode)",
            "allowNativeEditKey(event)",
            "noteImeEdit(KeyEvent.KEYCODE_DEL)",
            "noteImeEdit(KeyEvent.KEYCODE_ENTER)",
            "IME_NATIVE_PAIR_MS = 100L",
            'claimImeSpace("commit")',
            'claimImeEnter("action")',
            "imeWakePending.compareAndSet(false, true)",
            "private void wakeImeLoop()",
            "private void enqueueSafResult(String value)",
            "private void enqueueIntentPath(String value)",
            "runOnUiThread(this::wakeImeLoop)",
        ),
        "Android physical editing-key deduplication",
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
        saf_bridge,
        (
            "retry_after: HashMap<String, Instant>",
            "schedule_save_retry(tracked, &candidate, now)",
            'log::warn!("Deferred SAF save for {candidate}; will retry:',
        ),
        "SAF auto-sync retry/backoff",
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
            "fn touch_gesture_active(ui: &Ui) -> bool",
            "app.canvas.cancel_text_drag();",
            "surrendered_focus: false,",
            "response.surrender_focus();",
            "app.request_ime_hide = true;",
            "canvas_response(app, ui, content, scroll_target)",
            "if !app.canvas.surrendered_focus",
        ),
        "WordCraft canvas IME integration",
    )
    require(
        canvas,
        (
            "fn touch_gesture_active(ui: &Ui) -> bool",
            "app.canvas.cancel_text_drag();",
        ),
        "WordCraft two-finger scroll gesture guard",
    )

    # Use the pinned ArtCraft Android winit backend as the single source of truth for
    # touchscreen multi-touch gestures and hardware touchpad classification. Do not layer a
    # second centroid tracker in egui-winit or a generic ACTION_SCROLL -> LineDelta shim on top:
    # both bypass device classification and can turn precise touchpad pixels into wheel notches.
    android_winit = builder / "vendor/winit/src/platform_impl/android/mod.rs"
    android_device_kind = builder / "vendor/winit/src/platform_impl/android/device_kind.rs"
    require(
        android_winit,
        (
            "android_app.enable_motion_axis(Axis::Vscroll);",
            "android_app.enable_motion_axis(Axis::Hscroll);",
            "Classification::TwoFingerSwipe",
            "Classification::MultiFingerSwipe",
            "self.recognise_touch_gesture(motion_event)",
            "device_kind::classify(",
            "MotionAction::Scroll",
            "MouseScrollDelta::PixelDelta",
            "MouseScrollDelta::LineDelta",
            "TouchPhase::Cancelled",
        ),
        "stable Android touchscreen and touchpad gesture backend",
    )
    require(
        android_device_kind,
        (
            "pub(crate) fn classify(source: u32, tool: Tool) -> DeviceKind",
            "a_touchpad_is_a_pointer_that_scrolls_smoothly",
            "a_mouse_source_with_a_fingers_tool_is_a_touchpad",
            "the_glass_is_never_a_pointer",
        ),
        "Android mouse/touchpad device classification and tests",
    )

    # Android is neither Linux desktop nor a typical Unix filesystem. The upstream
    # system_font_dirs() fell through to /usr/share/fonts, which is absent on Android,
    # so the font catalog could never enumerate Android's installed system families.
    font_names = source / "crates/fonts/src/fontdb/names.rs"
    replace_once(
        font_names,
        '''    if cfg!(target_os = "macos") {''',
        '''    if cfg!(target_os = "android") {
        // Read-only platform font directories exposed to ordinary Android applications.
        // Include vendor/product partitions because OEMs often keep additional families there.
        dirs.extend([
            "/system/fonts",
            "/system_ext/fonts",
            "/product/fonts",
            "/vendor/fonts",
            "/odm/fonts",
        ].map(Into::into));
        if let Some(h) = &home {
            dirs.push(h.join("fonts"));
            dirs.push(h.join(".local/share/fonts"));
        }
    } else if cfg!(target_os = "macos") {''',
        "Android system font catalog directories",
    )
    require(
        font_names,
        (
            'if cfg!(target_os = "android")',
            '"/system/fonts"',
            '"/system_ext/fonts"',
            '"/product/fonts"',
            '"/vendor/fonts"',
            '"/odm/fonts"',
        ),
        "Android system font catalog",
    )
    integrate_android_icon_pack(builder, source)

    print(
        "Applied and verified WordCraft Android compatibility patches "
        f"against {WORDCRAFT_COMMIT}."
    )


if __name__ == "__main__":
    main()
