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

static bool TryLoadUiTable(const std::string& path) {
    auto initData = std::make_shared<Ship::ResourceInitData>();
    initData->Format = RESOURCE_FORMAT_BINARY;
    initData->Type = static_cast<uint32_t>(Ship::ResourceType::Json);
    initData->ResourceVersion = 0;

    try {
        auto resource = std::static_pointer_cast<Ship::Json>(
            Ship::Context::GetInstance()->GetResourceManager()->LoadResource(path, true, initData));
        if (resource == nullptr) {
            return false;
        }
        uiTranslation = resource->Data;
        return !uiTranslation.is_null();
    } catch (const std::exception& e) {
        SPDLOG_INFO("No UI translation table at {}: {}", path, e.what());
        return false;
    }
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

    auto entry = uiTranslation.find(visible);
    if (entry == uiTranslation.end() || !entry->is_string()) {
        return key;
    }
    // A translated label must keep its "##id" suffix or ImGui would treat the same
    // control as a new one, which can end in duplicate-ID asserts.
    return entry->get<std::string>() + (idSeparator == std::string::npos ? std::string() : key.substr(idSeparator));
}

static void RegisterUiTranslation() {
    InitUiTranslation();
    GameInteractor::Instance->RegisterGameHook<GameInteractor::OnSetGameLanguage>([]() { InitUiTranslation(); });
}

static RegisterShipInitFunc initFunc(RegisterUiTranslation);

} // namespace SohGui
