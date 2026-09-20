#ifndef SOH_STATS_H
#define SOH_STATS_H

#include <libultraship/libultraship.h>
#include "soh/SohGui/LocalizedWindow.h"

class SohStatsWindow final : public SohGui::LocalizedWindow {
  public:
    using LocalizedWindow::LocalizedWindow;
    ~SohStatsWindow(){};

  protected:
    void InitElement() override{};
    void DrawElement() override;
    void UpdateElement() override{};
};

#endif // SOH_STATS_H
