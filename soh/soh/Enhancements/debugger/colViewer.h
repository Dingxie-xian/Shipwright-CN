#pragma once

#include <libultraship/libultraship.h>
#include "soh/SohGui/LocalizedWindow.h"

typedef enum { COLVIEW_DISABLED, COLVIEW_SOLID, COLVIEW_TRANSPARENT } ColViewerRenderSetting;

#ifdef __cplusplus
class ColViewerWindow final : public SohGui::LocalizedWindow {
  public:
    using LocalizedWindow::LocalizedWindow;

    void InitElement() override;
    void DrawElement() override;
    void UpdateElement() override{};
};

#endif
