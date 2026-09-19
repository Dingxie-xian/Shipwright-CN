#include "SohStatsWindow.h"
#include "soh/OTRGlobals.h"
#include "soh/SohGui/UiTranslation.h"

void SohStatsWindow::DrawElement() {
    const float framerate = ImGui::GetIO().Framerate;
    const float deltatime = ImGui::GetIO().DeltaTime;
    ImGui::PushFont(OTRGlobals::Instance->fontMonoLarger);
    ImGui::PushStyleColor(ImGuiCol_Border, ImVec4(0, 0, 0, 0));

#if defined(_WIN32)
    ImGui::TextUnformatted(SohGui::Tr("Platform: Windows").c_str());
#elif defined(__IOS__)
    ImGui::TextUnformatted(SohGui::Tr("Platform: iOS").c_str());
#elif defined(__APPLE__)
    ImGui::TextUnformatted(SohGui::Tr("Platform: macOS").c_str());
#elif defined(__linux__)
    ImGui::TextUnformatted(SohGui::Tr("Platform: Linux").c_str());
#else
    ImGui::TextUnformatted(SohGui::Tr("Platform: Unknown").c_str());
#endif
    ImGui::Text(SohGui::Tr("Status: %0.3f ms/frame (%0.1f FPS)").c_str(), deltatime * 1000.0f, framerate);
    ImGui::PopStyleColor();
    ImGui::PopFont();
}
