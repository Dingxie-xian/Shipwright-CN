#!/usr/bin/env python3
"""Exercise the production window adapter against a small renderer test double."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
IMGUI = r'''
#pragma once
#include <cstdint>
#include <string>
using ImWchar = unsigned short;
struct ImVec2 { float x, y; ImVec2(float x_, float y_): x(x_), y(y_) {} };
constexpr int ImGuiWindowFlags_None = 0, ImGuiCond_FirstUseEver = 4;
namespace ImGui {
inline int begins=0, ends=0, sizes=0, flags=0, condition=0;
inline bool expanded=true, close=false;
inline ImVec2 size(-1,-1);
inline std::string title;
inline void SetNextWindowSize(ImVec2 s,int c) { size=s; condition=c; ++sizes; }
inline bool Begin(const char* t,bool* visible,uint32_t f) {
    title=t; flags=f; ++begins; if(close) *visible=false; return expanded;
}
inline void End() { ++ends; }
}
'''
BASE = r'''
#pragma once
#include <imgui.h>
namespace Ship {
class GuiWindow {
public:
    int syncs=0;
    GuiWindow(const std::string&,bool visible,const std::string& name,ImVec2,uint32_t)
        : mIsVisible(visible), mName(name) {}
    virtual ~GuiWindow()=default;
    virtual void Draw() {}
    virtual void DrawElement()=0;
    bool IsVisible() const { return mIsVisible; }
    std::string GetName() { return mName; }
protected:
    bool mIsVisible;
    void SyncVisibilityConsoleVariable() { ++syncs; }
private:
    std::string mName;
};
}
'''
TEST = r'''
#include <cassert>
#include <iostream>
#include "soh/soh/SohGui/LocalizedWindow.h"
namespace SohGui {
std::string TrLabel(const std::string& key) { return "translated###"+key; }
}
class Window : public SohGui::LocalizedWindow {
public:
    using LocalizedWindow::LocalizedWindow;
    int draws=0;
    void DrawElement() override { ++draws; }
};
int main() {
    Window hidden("window.hidden", "Original Name");
    hidden.Draw();
    assert(ImGui::begins==0 && hidden.draws==0 && hidden.syncs==0);
    Window shown("window.shown",true,"Audio Editor",ImVec2(820,630),123);
    shown.Draw();
    assert(shown.GetName()=="Audio Editor"); // Registry key must never be translated.
    assert(ImGui::title=="translated###Audio Editor");
    assert(ImGui::flags==123 && ImGui::size.x==820 && ImGui::size.y==630);
    assert(ImGui::condition==ImGuiCond_FirstUseEver && shown.draws==1 && shown.syncs==1);
    ImGui::expanded=false;
    shown.Draw();
    assert(ImGui::begins==2 && ImGui::ends==2 && shown.draws==1 && shown.syncs==2);
    ImGui::expanded=true;
    ImGui::close=true;
    shown.Draw();
    assert(!shown.IsVisible() && shown.syncs==3);
    shown.Draw();
    assert(ImGui::begins==3 && ImGui::ends==3 && shown.syncs==3);
    std::cout << "PASS: raw registry name, title, initial size, flags, collapsed/hidden/closed lifecycle\n";
}
'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cxx',default=os.environ.get('CXX','g++'))
    parser.add_argument('--build-dir',type=Path)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(dir=args.build_dir) as directory:
        temp=Path(directory)
        (temp/'ship/window/gui').mkdir(parents=True)
        (temp/'imgui.h').write_text(IMGUI,encoding='utf-8')
        (temp/'ship/window/gui/GuiWindow.h').write_text(BASE,encoding='utf-8')
        (temp/'test.cpp').write_text(TEST,encoding='utf-8')
        exe=temp/('window.exe' if os.name=='nt' else 'window')
        subprocess.run([args.cxx,'-std=c++17','-Wall','-Wextra','-Werror','-I',str(temp),'-I',str(ROOT),
                        str(temp/'test.cpp'),'-o',str(exe)],check=True)
        env=os.environ.copy()
        if Path(args.cxx).is_absolute():
            env['PATH']=str(Path(args.cxx).parent)+os.pathsep+env.get('PATH','')
        subprocess.run([str(exe)],check=True,env=env)


if __name__=='__main__':
    main()
