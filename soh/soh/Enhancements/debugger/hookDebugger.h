#ifndef hookDebugger_h
#define hookDebugger_h

#include <libultraship/libultraship.h>
#include "soh/SohGui/LocalizedWindow.h"

class HookDebuggerWindow final : public SohGui::LocalizedWindow {
  public:
    using LocalizedWindow::LocalizedWindow;

    void InitElement() override;
    void DrawElement() override;
    void UpdateElement() override{};
};

#endif // hookDebugger_h
