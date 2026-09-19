#!/usr/bin/env python3
"""Subset the UI font down to the characters an ImGui window can actually draw.

soh/assets/custom/fonts/SourceHanSansSC-Regular.otf is merged into every ImGui
font at startup. Shipping the complete 16 MB face would add all of it to soh.o2r
for glyphs that are unreachable: ImGui only builds glyphs that fall inside the
range handed to AddFontFromMemoryTTF, and that range is
GetGlyphRangesChineseSimplifiedCommon() — the 2500 most common simplified
characters plus Latin and punctuation, listed in imgui_common_chinese.txt.

This rewrites the committed font as a subset covering exactly that range, plus
every character used by a lang/ui_*.json translation so a menu string can never
fall outside it. That makes the font self-sufficient: nothing else needs to be
downloaded for a fully Chinese menu.

Run after adding translations, or --check to verify the committed font still
covers them without rewriting anything.

Usage:
    uv run message/generate_ui_font_subset.py
    uv run message/generate_ui_font_subset.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from fontTools import subset
except ImportError:
    print("fontTools not installed. Run: uv sync")
    sys.exit(1)

# The report prints the characters it complains about, which a Windows console
# code page cannot encode.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent           # scripts/chinese/message/
REPO = HERE.parent.parent.parent                 # Shipwright-CN/
FONT_IN = HERE / "charmap" / "SourceHanSansSC-Regular.otf"
RANGE_FILE = HERE / "imgui_common_chinese.txt"
LANG_DIR = REPO / "soh" / "assets" / "custom" / "lang"
FONT_OUT = REPO / "soh" / "assets" / "custom" / "fonts" / "SourceHanSansSC-Regular.otf"


def chars_from_range_file() -> set[str]:
    """The characters ImGui asks the font for, comments stripped.

    Control characters are dropped: ImGui never draws them, and cmap coverage of
    them is optional, so requiring them would make --check fail for no reason.
    """
    text = RANGE_FILE.read_text(encoding="utf-8")
    return {c for line in text.splitlines() if not line.startswith("#") for c in line
            if c.isprintable()}


def chars_from_lang_tables() -> tuple[set[str], int]:
    """Every character of every translation value, across all languages."""
    chars: set[str] = set()
    files = sorted(LANG_DIR.glob("ui_*.json"))
    for path in files:
        table = json.loads(path.read_text(encoding="utf-8"))
        for key, value in table.items() if isinstance(table, dict) else []:
            if isinstance(value, str):
                # Newlines and tabs are layout, not glyphs.
                chars.update(c for c in value if c.isprintable())
    return chars, len(files)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="only verify the committed font, do not rewrite it")
    args = parser.parse_args()

    ranged = chars_from_range_file()
    translated, table_count = chars_from_lang_tables()
    wanted = ranged | translated

    print(f"ImGui range: {len(ranged)} characters")
    print(f"{table_count} translation table(s): {len(translated)} distinct characters")
    print(f"font must cover: {len(wanted)} characters")

    if args.check:
        # What has to hold is that every character a translation can put on screen
        # has a glyph. Coverage of the rest of ImGui's range is reported but not
        # required: Source Han Sans has no outline for a few dozen rare punctuation
        # marks, and ImGui skips a missing glyph rather than failing.
        from fontTools.ttLib import TTFont

        if not FONT_OUT.exists():
            print(f"\nCommitted font not found: {FONT_OUT}")
            return 1
        with TTFont(str(FONT_OUT), lazy=True) as committed:
            covered = set()
            for table in committed["cmap"].tables:
                covered.update(chr(code) for code in table.cmap)

        missing = sorted(translated - covered)
        if missing:
            print(f"\n{len(missing)} translated character(s) have no glyph:")
            print("  " + " ".join(missing))
            print("  Run: uv run message/generate_ui_font_subset.py")
            return 1

        uncovered = ranged - covered
        print(f"\nOK: every translated character has a glyph")
        if uncovered:
            print(f"    ({len(uncovered)} unused range characters have no outline in the source font)")
        return 0

    if not FONT_IN.exists():
        print(f"\nInput font not found: {FONT_IN}")
        print("  Download: https://github.com/adobe-fonts/source-han-sans/releases")
        return 1

    options = subset.Options()
    # Keep only the tables stb_truetype needs. The menus never use OpenType layout
    # features, and desubroutinizing keeps the CFF outlines small and parseable.
    options.drop_tables += ["GSUB", "GPOS", "GDEF", "DSIG", "BASE", "JSTF", "MATH", "SVG "]
    options.desubroutinize = True
    options.hinting = False
    options.notdef_outline = True

    font = subset.load_font(str(FONT_IN), options)
    try:
        subsetter = subset.Subsetter(options=options)
        subsetter.populate(text="".join(sorted(wanted)))
        subsetter.subset(font)
        FONT_OUT.parent.mkdir(parents=True, exist_ok=True)
        subset.save_font(font, str(FONT_OUT), options)
    finally:
        font.close()

    before = FONT_IN.stat().st_size
    after = FONT_OUT.stat().st_size
    print(f"\n{FONT_OUT.relative_to(REPO)}")
    print(f"  {before / 1024 / 1024:.1f} MB -> {after / 1024:.0f} KB ({after / before * 100:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
