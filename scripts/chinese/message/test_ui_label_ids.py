#!/usr/bin/env python3
"""Compile the production label function in isolation and test its ID contract.

The translator is a test double with deliberate duplicate display names. This
tests the actual TrLabel body without building the renderer or needing a ROM.
Full popup/control behavior still needs an interactive game smoke test.
"""
import argparse
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HARNESS = r'''
#include <cassert>
#include <iostream>
#include <string>
#include <unordered_map>
namespace SohGui {
bool chinese = true;
std::string Tr(const std::string& key) {
    const std::unordered_map<std::string, std::string> table = {
        { "On", "enabled" }, { "Enable", "enabled" },
        { "Clear All", "clear translated" }, { "Audio Options", "audio translated" }
    };
    auto found = table.find(key);
    return chinese && found != table.end() ? found->second : key;
}
PRODUCTION_FUNCTION
}
int main() {
    using namespace SohGui;
    assert(TrLabel("").empty());
    assert(TrLabel("##input") == "##input");
    assert(TrLabel("###input") == "###input");
    assert(TrLabel("On") == "enabled###On");
    assert(TrLabel("Enable") == "enabled###Enable");
    assert(TrLabel("On") != TrLabel("Enable"));
    assert(TrLabel("On##left") != TrLabel("On##right"));
    assert(TrLabel("Clear All###popup") == "clear translated###popup");
    assert(TrLabel("Clear All##popup") == "clear translated###Clear All##popup");
    assert(TrLabel("User Track") == "User Track###User Track");
    const auto chineseTab = TrLabel("Audio Options");
    chinese = false;
    const auto englishTab = TrLabel("Audio Options");
    assert(chineseTab.substr(chineseTab.find("###")) == englishTab.substr(englishTab.find("###")));
    assert(TrLabel("Clear All###popup") == "Clear All###popup");
    assert(TrLabel("On##left") == "On###On##left");
    std::cout << "PASS: label collisions, explicit IDs, hidden IDs, missing keys and language switching\n";
}
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cxx', default=os.environ.get('CXX', 'g++'))
    parser.add_argument('--build-dir', type=Path)
    args = parser.parse_args()
    source = (ROOT / 'soh/soh/SohGui/UiTranslation.cpp').read_text(encoding='utf-8')
    body = re.search(r'^std::string TrLabel\([^\n]*\) \{[\s\S]*?^\}', source, re.MULTILINE)
    if body is None:
        raise RuntimeError('Could not find production TrLabel function')
    with tempfile.TemporaryDirectory(dir=args.build_dir) as temp:
        temp = Path(temp)
        cpp = temp / 'ui_labels.cpp'
        exe = temp / ('ui_labels.exe' if os.name == 'nt' else 'ui_labels')
        cpp.write_text(HARNESS.replace('PRODUCTION_FUNCTION', body.group()), encoding='utf-8')
        subprocess.run([args.cxx, '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(exe)], check=True)
        env = os.environ.copy()
        if Path(args.cxx).is_absolute():
            env['PATH'] = str(Path(args.cxx).parent) + os.pathsep + env.get('PATH', '')
        subprocess.run([str(exe)], check=True, env=env)


if __name__ == '__main__':
    main()
