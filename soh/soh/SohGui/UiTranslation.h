#ifndef UI_TRANSLATION_H
#define UI_TRANSLATION_H

#include <string>
#include <imgui.h>

namespace SohGui {

// Loads the menu translation table for the language selected in settings.
// Safe to call again after a language change, and safe when no table exists for
// the selected language — every lookup then falls back to the original English.
void InitUiTranslation();

// Returns the translation for `key`, or `key` unchanged when there is none.
// ImGui gives "label##id" a special meaning, so a "##..." suffix is preserved
// verbatim and only the visible part before it is translated.
std::string Tr(const std::string& key);

// For ImGui labels only: display translated text but derive identity from the
// original key. Unlike ##, ### excludes the visible text from ImGui's hash.
// Use Tr() for ordinary text and format strings, which must not contain an ID.
std::string TrLabel(const std::string& key);

// Glyph range for the CJK merge: ImGui's common simplified Chinese set extended
// with every character the translation tables use. ImGui only builds the glyphs
// that fall inside the range it is given, so without the extension a translated
// character outside its hardcoded set would render blank whatever the font.
// Built on first use; the returned pointer is owned by this module.
const ImWchar* GetUiGlyphRanges();

} // namespace SohGui

#endif
