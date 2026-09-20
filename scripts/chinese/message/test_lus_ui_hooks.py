#!/usr/bin/env python3
"""Test patch applicability and the production LUS translation/window contract.

Renderer calls and configuration persistence are test doubles. The window
declarations, translation callbacks, Draw and GetName bodies are real patched
source. The game build and interactive menu checks remain separate gates.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from validate_ui_translations import calls, literal, PRINTF

ROOT = Path(__file__).resolve().parents[3]
FILES = (
    'include/ship/window/gui/GuiWindow.h',
    'src/ship/window/gui/GuiWindow.cpp',
    'src/ship/window/gui/ConsoleWindow.cpp',
    'src/libultraship/window/gui/GfxDebuggerWindow.cpp',
)
IMGUI = r'''
#pragma once
#include <cstdint>
#include <string>
struct ImVec2 { float x,y; ImVec2(float a=0,float b=0):x(a),y(b){} };
inline bool operator!=(ImVec2 a,ImVec2 b) { return a.x!=b.x || a.y!=b.y; }
struct ImRect {};
template<class T> struct ImVector {};
constexpr int ImGuiCond_FirstUseEver=4;
namespace ImGui {
inline int begins=0,ends=0,sizes=0,flags=0,condition=0;
inline bool expanded=true,close=false;
inline ImVec2 size;
inline std::string title;
inline void SetNextWindowSize(ImVec2 s,int c){size=s;condition=c;++sizes;}
inline bool Begin(const char* t,bool* visible,uint32_t f){title=t;flags=f;++begins;if(close)*visible=false;return expanded;}
inline void End(){++ends;}
}
'''
ELEMENT = r'''
#pragma once
namespace Ship {
class GuiElement {
public:
    GuiElement(bool visible=false):mIsVisible(visible){}
    virtual ~GuiElement()=default;
    virtual void Draw()=0;
    virtual void DrawElement()=0;
    bool IsVisible() const{return mIsVisible;}
protected:
    virtual void SetVisibility(bool visible){mIsVisible=visible;}
    bool mIsVisible;
};
}
'''
HARNESS = r'''
#include <cassert>
#include <iostream>
#include "ship/window/gui/GuiWindow.h"
namespace Ship {
PRODUCTION_CALLBACKS
// Configuration IO is unchanged by the patch; isolate it from this GUI test.
int syncs=0;
GuiWindow::GuiWindow(const std::string& cvar,bool visible,const std::string& name,ImVec2 size,uint32_t flags)
    :GuiElement(visible),mName(name),mVisibilityConsoleVariable(cvar),mOriginalSize(size),mWindowFlags(flags){}
void GuiWindow::SyncVisibilityConsoleVariable(){++syncs;}
PRODUCTION_VISIBILITY
PRODUCTION_DRAW
PRODUCTION_GET_NAME
}
class TestWindow:public Ship::GuiWindow {
public:
    using GuiWindow::GuiWindow;
    int draws=0;
    void DrawElement() override{++draws;}
};
std::string Text(const std::string& key){return "text:"+key;}
std::string Label(const std::string& key){return "translated###"+key;}
int main(){
    using Ship::GuiWindow;
    assert(GuiWindow::TranslateText("Debug")=="Debug");
    assert(GuiWindow::TranslateLabel("Clear##id")=="Clear##id");
    TestWindow hidden("hidden",false,"Hidden",ImVec2(-1,-1),0);
    hidden.Draw();
    assert(ImGui::begins==0 && Ship::syncs==0);
    TestWindow shown("window",true,"Audio Editor",ImVec2(820,630),123);
    shown.Draw();
    assert(ImGui::title=="Audio Editor");
    GuiWindow::SetTextTranslators(Text,Label);
    assert(GuiWindow::TranslateText("Debug")=="text:Debug");
    assert(GuiWindow::TranslateLabel("Clear##id")=="translated###Clear##id");
    shown.Draw();
    assert(shown.GetName()=="Audio Editor");
    assert(ImGui::title=="translated###Audio Editor");
    assert(ImGui::flags==123 && ImGui::size.x==820 && ImGui::size.y==630);
    assert(ImGui::condition==ImGuiCond_FirstUseEver && shown.draws==2 && Ship::syncs==2);
    ImGui::expanded=false;
    shown.Draw();
    assert(ImGui::begins==3 && ImGui::ends==3 && shown.draws==2 && Ship::syncs==3);
    ImGui::expanded=true; ImGui::close=true;
    shown.Draw();
    assert(!shown.IsVisible() && Ship::syncs==4);
    shown.Draw();
    assert(ImGui::begins==4 && ImGui::ends==4 && Ship::syncs==4);
    GuiWindow::SetTextTranslators(nullptr,nullptr);
    assert(GuiWindow::TranslateText("Debug")=="Debug");
    assert(GuiWindow::TranslateLabel("Clear##id")=="Clear##id");
    std::cout<<"PASS: fallback, callbacks, raw registry names, flags, size and window lifecycle\n";
}
'''


def function(source, name):
    found = re.search(r'^(?:void|std::string) GuiWindow::' + name + r'\([^\n]*\) \{[\s\S]*?^\}',
                      source, re.MULTILINE)
    if found is None:
        raise RuntimeError('Missing production function: ' + name)
    return found.group()


def check_translations(source_dir):
    table = json.loads((ROOT / 'soh/assets/custom/lang/ui_chi.json').read_text(encoding='utf-8'))
    keys = set()
    for rel in FILES[1:]:
        source = (source_dir / rel).read_text(encoding='utf-8')
        for name, _, args in calls(source):
            if args and (name.endswith(('::TranslateText', '::TranslateLabel')) or name == 'showColor'):
                key = literal(args[0])
                if key is not None:
                    keys.add(key.split('##')[0])
    missing = sorted(k for k in keys if k and k not in table)
    if missing:
        raise RuntimeError('Untranslated library captions: ' + repr(missing))
    for key in keys:
        if key in table and '%' in key and PRINTF.findall(key) != PRINTF.findall(table[key]):
            raise RuntimeError('Library printf argument mismatch: ' + key)
    print(f'PASS: {len(keys)} library menu captions and their format arguments', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', type=Path, default=ROOT / 'libultraship')
    parser.add_argument('--cmake', default='cmake')
    parser.add_argument('--cxx', default=os.environ.get('CXX', 'g++'))
    parser.add_argument('--build-dir', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(dir=args.build_dir) as directory:
        temp = Path(directory)
        fixture = temp / 'lus'
        for rel in FILES:
            dest = fixture / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(args.sources / rel, dest)
        command = [args.cmake, '-DSOH_LUS_UI_SOURCE_DIR=' + str(fixture), '-P',
                   str(ROOT / 'CMake/lus-ui-translation.cmake')]
        subprocess.run(command, check=True, capture_output=True)
        first = {rel: (fixture / rel).read_bytes() for rel in FILES}
        subprocess.run(command, check=True, capture_output=True)
        assert first == {rel: (fixture / rel).read_bytes() for rel in FILES}, 'Reconfiguration changed the patch'
        print('PASS: patch applies and repeated CMake configuration is idempotent', flush=True)
        check_translations(fixture)
        source = (fixture / FILES[1]).read_text(encoding='utf-8')
        callbacks = source.split('namespace Ship {\n', 1)[1].split('GuiWindow::GuiWindow(', 1)[0]
        harness = HARNESS.replace('PRODUCTION_CALLBACKS', callbacks)
        harness = harness.replace('PRODUCTION_VISIBILITY', function(source, 'SetVisibility'))
        harness = harness.replace('PRODUCTION_DRAW', function(source, 'Draw'))
        harness = harness.replace('PRODUCTION_GET_NAME', function(source, 'GetName'))
        include = temp / 'headers'
        (include / 'ship/window/gui').mkdir(parents=True)
        (include / 'imgui.h').write_text(IMGUI, encoding='utf-8')
        (include / 'imgui_internal.h').write_text('#pragma once\n', encoding='utf-8')
        (include / 'ship/window/gui/GuiElement.h').write_text(ELEMENT, encoding='utf-8')
        shutil.copyfile(fixture / FILES[0], include / 'ship/window/gui/GuiWindow.h')
        cpp = temp / 'test.cpp'
        exe = temp / ('test.exe' if os.name == 'nt' else 'test')
        cpp.write_text(harness, encoding='utf-8')
        subprocess.run([args.cxx, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-I', str(include),
                        str(cpp), '-o', str(exe)], check=True)
        env = os.environ.copy()
        if Path(args.cxx).is_absolute():
            env['PATH'] = str(Path(args.cxx).parent) + os.pathsep + env.get('PATH', '')
        subprocess.run([str(exe)], check=True, env=env)
        # A dependency update that changes the patched contract must fail closed.
        header = fixture / FILES[0]
        header.write_text(header.read_text(encoding='utf-8').replace('SetTextTranslators', 'UnsupportedTranslator'), encoding='utf-8')
        result = subprocess.run(command, capture_output=True)
        assert result.returncode != 0, 'Mismatched dependency was silently accepted'
        print('PASS: incompatible dependency changes are rejected', flush=True)


if __name__ == '__main__':
    main()
