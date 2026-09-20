#include <libultraship/libultraship.h>
#include "soh/SohGui/LocalizedWindow.h"

class TimeDisplayWindow final : public SohGui::LocalizedWindow {
  public:
    using LocalizedWindow::LocalizedWindow;

    void InitElement() override;
    void DrawElement() override{};
    void Draw() override;
    void UpdateElement() override{};
};

void TimeDisplayUpdateDisplayOptions();
void TimeDisplayInitSettings();

typedef enum TimerDisplay {
    DISPLAY_IN_GAME_TIMER,
    DISPLAY_TIME_OF_DAY,
    DISPLAY_CONDITIONAL_TIMER,
    DISPLAY_NAVI_TIMER,
} TimerDisplay;

typedef enum NaviTimerValues {
    NAVI_PREPARE = 600,
    NAVI_ACTIVE = 3000,
    NAVI_COOLDOWN = 25800,
    DAY_BEGINS = 17759,
    NIGHT_BEGINS = 49155
} NaviTimerValues;

typedef struct {
    uint32_t timeID;
    std::string timeLabel;
    const char* timeEnable;
} TimeObject;

extern const std::vector<TimeObject> timeDisplayList;
