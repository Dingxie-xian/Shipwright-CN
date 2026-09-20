#include "UiTranslation.h"

#include <libultraship/libultraship.h>
#include <nlohmann/json.hpp>
#include <ship/resource/type/Json.h>
#include <spdlog/spdlog.h>

#include "soh/Enhancements/game-interactor/GameInteractor.h"
#include "soh/ShipInit.hpp"
#include "soh/cvar_prefixes.h"

extern "C" {
#include "z64.h"
}

namespace SohGui {

// Translations live in data files rather than in code: they are packed into soh.o2r
// from assets/custom/lang/, so adding a language or fixing a wording never needs a
// recompile of the surrounding call sites, and no source file has to be switched to
// /utf-8 just to hold non-ASCII literals.
static nlohmann::json uiTranslation = nullptr;

// ImGui only builds glyphs that fall inside the glyph range it is handed, so a
// character missing from that range renders blank no matter how complete the font
// is. ImGui's own Chinese set is the 2500 most common characters from a 1987 word
// frequency list, which does not even cover 频 or 屏, so the tables are merged in.
static ImVector<ImWchar> uiGlyphRanges;
static bool uiGlyphRangesBuilt = false;

static const char* UiLanguageSuffix(int32_t language) {
    switch (language) {
        case LANGUAGE_GER:
            return "_ger";
        case LANGUAGE_FRA:
            return "_fra";
        case LANGUAGE_JPN:
            return "_jpn";
        case LANGUAGE_CHI:
            return "_chi";
        default:
            // English is the source language for every key, so it needs no table.
            return nullptr;
    }
}

static nlohmann::json LoadUiTable(const std::string& path) {
    auto initData = std::make_shared<Ship::ResourceInitData>();
    initData->Format = RESOURCE_FORMAT_BINARY;
    initData->Type = static_cast<uint32_t>(Ship::ResourceType::Json);
    initData->ResourceVersion = 0;

    try {
        auto resource = std::static_pointer_cast<Ship::Json>(
            Ship::Context::GetInstance()->GetResourceManager()->LoadResource(path, true, initData));
        if (resource == nullptr) {
            return nullptr;
        }
        return resource->Data;
    } catch (const std::exception& e) {
        SPDLOG_INFO("No UI translation table at {}: {}", path, e.what());
        return nullptr;
    }
}

static bool TryLoadUiTable(const std::string& path) {
    uiTranslation = LoadUiTable(path);
    if (!uiTranslation.is_object()) {
        uiTranslation = nullptr;
        return false;
    }
    return true;
}

void InitUiTranslation() {
    uiTranslation = nullptr;

    const char* suffix = UiLanguageSuffix(CVarGetInteger(CVAR_SETTING("Languages"), LANGUAGE_ENG));
    if (suffix == nullptr) {
        return;
    }
    TryLoadUiTable(std::string("lang/ui") + suffix + ".json");
}

std::string Tr(const std::string& key) {
    if (uiTranslation.is_null()) {
        return key;
    }

    const size_t idSeparator = key.find("##");
    const std::string visible = idSeparator == std::string::npos ? key : key.substr(0, idSeparator);
    if (visible.empty()) {
        return key;
    }

    auto entry = uiTranslation.find(visible);
    if (entry == uiTranslation.end() || !entry->is_string()) {
        return key;
    }
    // Preserve suffixes for callers that format their own labels. TrLabel also
    // excludes translated text from the ImGui ID; preserving ## alone does not.
    return entry->get<std::string>() + (idSeparator == std::string::npos ? std::string() : key.substr(idSeparator));
}

std::string TrLabel(const std::string& key) {
    const size_t separator = key.find("##");
    if (separator == 0 || key.empty()) {
        return key; // Already an invisible ID.
    }
    const std::string visible = key.substr(0, separator);
    const size_t stableId = key.find("###");
    const std::string suffix = stableId == std::string::npos ? "###" + key : key.substr(stableId);
    return Tr(visible) + suffix;
}

const ImWchar* GetUiGlyphRanges() {
    if (uiGlyphRangesBuilt) {
        return uiGlyphRanges.Data;
    }
    uiGlyphRangesBuilt = true;

    ImFontGlyphRangesBuilder builder;
    builder.AddRanges(ImGui::GetIO().Fonts->GetGlyphRangesChineseSimplifiedCommon());

    // Every table, not just the selected one: the font atlas is built once at
    // startup, so a language switched to later still has to find its glyphs there.
    for (const char* suffix : { "_ger", "_fra", "_jpn", "_chi" }) {
        const nlohmann::json table = LoadUiTable(std::string("lang/ui") + suffix + ".json");
        if (table.is_null() || !table.is_object()) {
            continue;
        }
        for (const auto& [key, value] : table.items()) {
            if (value.is_string()) {
                const std::string text = value.get<std::string>();
                builder.AddText(text.c_str());
            }
        }
    }

    builder.BuildRanges(&uiGlyphRanges);
    return uiGlyphRanges.Data;
}

static void RegisterUiTranslation() {
    InitUiTranslation();
    GameInteractor::Instance->RegisterGameHook<GameInteractor::OnSetGameLanguage>([]() { InitUiTranslation(); });
}

static RegisterShipInitFunc initFunc(RegisterUiTranslation);

} // namespace SohGui
