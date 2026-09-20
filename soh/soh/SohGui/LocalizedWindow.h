#pragma once

#ifdef __cplusplus

#include <ship/window/gui/GuiWindow.h>
#include "UiTranslation.h"

namespace SohGui {

// The upstream window name also identifies it in Gui's registry. Keep that
// name unchanged and translate only the title passed to ImGui when drawing.
class LocalizedWindow : public Ship::GuiWindow {
  public:
    LocalizedWindow(const std::string& cvar, bool visible, const std::string& name,
                    ImVec2 size = ImVec2(-1, -1), uint32_t flags = ImGuiWindowFlags_None)
        : Ship::GuiWindow(cvar, visible, name, size, flags), mInitialSize(size), mFlags(flags) {
    }

    LocalizedWindow(const std::string& cvar, const std::string& name, ImVec2 size = ImVec2(-1, -1),
                    uint32_t flags = ImGuiWindowFlags_None)
        : LocalizedWindow(cvar, false, name, size, flags) {
    }

    void Draw() override {
        if (!IsVisible()) {
            return;
        }
        if (mInitialSize.x != -1 || mInitialSize.y != -1) {
            ImGui::SetNextWindowSize(mInitialSize, ImGuiCond_FirstUseEver);
        }
        if (ImGui::Begin(TrLabel(GetName()).c_str(), &mIsVisible, mFlags)) {
            DrawElement();
        }
        ImGui::End();
        SyncVisibilityConsoleVariable();
    }

  private:
    ImVec2 mInitialSize;
    uint32_t mFlags;
};

} // namespace SohGui

#endif // __cplusplus
