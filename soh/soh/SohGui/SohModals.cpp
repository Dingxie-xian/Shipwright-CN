#include "SohModals.h"
#include <imgui.h>
#include <vector>
#include <string>
#include <libultraship/bridge.h>
#include <libultraship/libultraship.h>
#include "UIWidgets.hpp"
#include "UiTranslation.h"
#include "SohGui.hpp"
#include "soh/OTRGlobals.h"
#include "z64.h"

extern "C" PlayState* gPlayState;
struct SohModal {
    std::string title_;
    std::string message_;
    std::string button1_;
    std::string button2_;
    std::function<void()> button1callback_;
    std::function<void()> button2callback_;
};
std::vector<SohModal> modals;

bool closePopup = false;

void SohModalWindow::Draw() {
    if (!IsVisible()) {
        return;
    }
    DrawElement();
    // Sync up the IsVisible flag if it was changed by ImGui
    SyncVisibilityConsoleVariable();
}

void SohModalWindow::DrawElement() {
    if (modals.size() > 0) {
        SohModal curModal = modals.at(0);
        // Popups are identified by their title, so the id is pinned to the untranslated
        // title while the visible part is the translation.
        const std::string titleLabel = SohGui::TrLabel(curModal.title_);
        if (!ImGui::IsPopupOpen(titleLabel.c_str())) {
            ImGui::OpenPopup(titleLabel.c_str());
        }
        if (closePopup) {
            ImGui::CloseCurrentPopup();
            modals.erase(modals.begin());
            closePopup = false;
        }
        ImGui::SetNextWindowPos(ImGui::GetMainViewport()->GetCenter(), ImGuiCond_Always, ImVec2(0.5f, 0.5f));
        if (ImGui::BeginPopupModal(titleLabel.c_str(), NULL,
                                   ImGuiWindowFlags_AlwaysAutoResize | ImGuiWindowFlags_NoResize |
                                       ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoScrollbar |
                                       ImGuiWindowFlags_NoSavedSettings)) {
            ImGui::Text("%s", SohGui::Tr(curModal.message_).c_str());
            UIWidgets::PushStyleButton(THEME_COLOR);
            const std::string button1Label = SohGui::TrLabel(curModal.button1_);
            if (ImGui::Button(button1Label.c_str())) {
                if (curModal.button1callback_ != nullptr) {
                    curModal.button1callback_();
                }
                ImGui::CloseCurrentPopup();
                modals.erase(modals.begin());
            }
            UIWidgets::PopStyleButton();
            if (curModal.button2_ != "") {
                ImGui::SameLine();
                UIWidgets::PushStyleButton(THEME_COLOR);
                const std::string button2Label = SohGui::TrLabel(curModal.button2_);
                if (ImGui::Button(button2Label.c_str())) {
                    if (curModal.button2callback_ != nullptr) {
                        curModal.button2callback_();
                    }
                    ImGui::CloseCurrentPopup();
                    modals.erase(modals.begin());
                }
                UIWidgets::PopStyleButton();
            }
            ImGui::EndPopup();
        }
    }
}

void SohModalWindow::RegisterPopup(std::string title, std::string message, std::string button1, std::string button2,
                                   std::function<void()> button1callback, std::function<void()> button2callback) {
    modals.push_back({ title, message, button1, button2, button1callback, button2callback });
}

size_t SohModalWindow::PopupsQueued() {
    return modals.size();
}

bool SohModalWindow::IsPopupOpen(std::string title) {
    return !modals.empty() && modals.at(0).title_ == title;
}

void SohModalWindow::DismissPopup() {
    closePopup = true;
}
