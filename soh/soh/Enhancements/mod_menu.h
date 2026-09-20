#pragma once

#include <libultraship/libultraship.h>
#include "soh/SohGui/LocalizedWindow.h"

#ifdef __cplusplus
class ModMenuWindow : public SohGui::LocalizedWindow {
  public:
    using LocalizedWindow::LocalizedWindow;

    void InitElement() override;
    void DrawElement() override;
    void UpdateElement() override{};
};
#endif