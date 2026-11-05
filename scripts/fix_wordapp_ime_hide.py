#!/usr/bin/env python3
"""Keep WordApp's IME-hide field wired through construction and window swapping.

ArtCraft's scrolling.sh adds request_ime_hide to WordApp after this patcher runs.
The field is app-wide, so WordApp::new must initialize it and swap_window must
explicitly ignore it while destructuring the app's per-window state.
"""
from __future__ import annotations

import sys
from pathlib import Path


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


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_wordapp_ime_hide.py WORDCRAFT_SOURCE")

    source = Path(sys.argv[1]).resolve()
    app = source / "crates/ui-egui/src/app.rs"
    window_ui = source / "crates/ui-egui/src/window_ui.rs"
    if not app.is_file() or not window_ui.is_file():
        raise SystemExit(f"Not a WordCraft source checkout: {source}")

    replace_once(
        app,
        "            synthetic_injected: 0,\\n            styled: false,",
        "            synthetic_injected: 0,\\n            request_ime_hide: false,\\n            styled: false,",
        "initialize app-wide Android IME-hide request",
    )
    replace_once(
        window_ui,
        "            synthetic_injected: _,\\n            // The current command's origin, set and cleared around it.",
        "            synthetic_injected: _,\\n            request_ime_hide: _,\\n            // The current command's origin, set and cleared around it.",
        "exclude app-wide Android IME-hide request from window swapping",
    )

    app_text = app.read_text(encoding="utf-8")
    window_text = window_ui.read_text(encoding="utf-8")
    if "request_ime_hide: false," not in app_text:
        raise SystemExit("WordApp constructor does not initialize request_ime_hide")
    if "request_ime_hide: _," not in window_text:
        raise SystemExit("WordApp::swap_window does not classify request_ime_hide as app-wide")
    print("Verified request_ime_hide initialization and app-wide destructuring.")
    

if __name__ == "__main__":
    main()
