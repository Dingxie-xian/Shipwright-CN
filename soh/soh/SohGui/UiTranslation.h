#ifndef UI_TRANSLATION_H
#define UI_TRANSLATION_H

#include <string>

namespace SohGui {

// Loads the menu translation table for the language selected in settings.
// Safe to call again after a language change, and safe when no table exists for
// the selected language — every lookup then falls back to the original English.
void InitUiTranslation();

// Returns the translation for `key`, or `key` unchanged when there is none.
// ImGui gives "label##id" a special meaning, so a "##..." suffix is preserved
// verbatim and only the visible part before it is translated.
std::string Tr(const std::string& key);

} // namespace SohGui

#endif
