#!/usr/bin/env python3
"""Check menu translations against actual C++ literals, formats and UI data.

Run from any directory. No third-party Python packages are required.
The font outlines are checked separately by generate_ui_font_subset.py --check.
"""
import json
import re
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOKEN = re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|(?:u8|[LuU])?"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_]\w*|::|[^\s]')
PRINTF = re.compile(r'%(?:%|[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|h|ll|l|j|z|t|L)?[diouxXeEfgGaAcsp])')


def tokenize(source):
    return [(m.group(), m.start(), m.end()) for m in TOKEN.finditer(source)
            if not m.group().startswith(('//', '/*'))]


def literal(tokens):
    parts = []
    for token, _, _ in tokens:
        if not re.fullmatch(r'(?:u8|[LuU])?"(?:\\.|[^"\\])*"', token):
            return None
        try:
            parts.append(json.loads(token[token.index('"'):]))
        except ValueError:
            return None  # Icon escapes/character literals are not translation keys.
    return ''.join(parts) if parts else None


def calls(source):
    tokens = tokenize(source)
    for i, (token, offset, _) in enumerate(tokens[:-1]):
        if not re.fullmatch(r'[A-Za-z_]\w*', token) or tokens[i + 1][0] != '(':
            continue
        name, k = token, i - 1
        while k > 0 and tokens[k][0] == '::':
            name = tokens[k - 1][0] + '::' + name
            k -= 2
        stack, args, first = ['('], [], i + 2
        for j in range(first, len(tokens)):
            value = tokens[j][0]
            if value in ('(', '[', '{'):
                stack.append(value)
            elif value in (')', ']', '}'):
                stack.pop()
                if not stack:
                    args.append(tokens[first:j])
                    yield name, offset, args
                    break
            elif value == ',' and len(stack) == 1:
                args.append(tokens[first:j])
                first = j + 1


def main():
    errors, pairs = [], []
    table = json.loads((ROOT / 'soh/assets/custom/lang/ui_chi.json').read_text(encoding='utf-8'),
                       object_pairs_hook=lambda items: pairs.extend(items) or dict(items))
    if len(pairs) != len(table):
        errors.append('Duplicate translation keys')
    for key, value in table.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f'Empty/non-string translation: {key!r}')
        elif '##' in value:
            errors.append(f'Translation changes ImGui identity: {key!r}')

    seen, formats, fmt_formats, audio, cosmetics = set(), set(), set(), set(), set()
    for path in sorted((ROOT / 'soh/soh').rglob('*')):
        if path.suffix not in ('.cpp', '.hpp', '.h'):
            continue
        source = path.read_text(encoding='utf-8')
        for name, offset, args in calls(source):
            if not args:
                continue
            if name in ('SohGui::Tr', 'SohGui::TrLabel'):
                key = literal(args[0])
                if key is not None:
                    seen.add(key.split('##')[0])
            if name.endswith('RegisterPopup'):
                for arg in args[:4]:
                    key = literal(arg)
                    if key:
                        seen.add(key)
            if name in ('SEQUENCE_MAP_ENTRY', 'COSMETIC_OPTION') and len(args) > 1:
                key = literal(args[1])
                if key:
                    (audio if name == 'SEQUENCE_MAP_ENTRY' else cosmetics).add(key)
                    seen.add(key)
            if name.startswith('UIWidgets::') or name in ('ImGui::Checkbox', 'ImGui::Button', 'ImGui::InputText'):
                # Labels such as "Rainbow##" + option.name are not literals as
                # a whole, but their visible prefix is still a dictionary key.
                for token in args[0]:
                    value = literal([token])
                    if value and '##' in value:
                        visible = value.split('##')[0]
                        if '%' not in visible and '{' not in visible:
                            seen.add(visible)
            # Find the literal supplied to an actual formatting call, including
            # Tr()/fmt::runtime() and concatenated C++ string literals.
            index = 1 if name == 'ImGui::TextColored' else 0
            printf_call = name in ('ImGui::Text', 'ImGui::TextWrapped', 'ImGui::TextColored',
                                  'ImGui::TextDisabled', 'ImGui::SetTooltip', 'ImGui::BulletText',
                                  'StringHelper::Sprintf', 'snprintf', 'sprintf')
            if (printf_call or name == 'fmt::format') and len(args) > index:
                arg = args[index]
                quoted = [token for token in arg if token[0].startswith('"')]
                key = literal(quoted)
                if key:
                    if printf_call:
                        formats.add(key)
                    else:
                        fmt_formats.add(key)
            # Widget labels are formatted by the slider/input wrappers.
            if 'Slider' in name and args:
                key = literal(args[0])
                if key:
                    formats.add(key)
        for m in re.finditer(r'\.name\s*=\s*((?:"(?:\\.|[^"\\])*"\s*)+)', source):
            key = literal(tokenize(m.group(1)))
            if key:
                seen.add(key.split('##')[0])
                formats.add(key)

    for key in seen:
        if re.search('[A-Za-z]', key) and key not in table:
            errors.append(f'Missing displayed translation: {key!r}')
    checked_printf, checked_fmt = 0, 0
    for key in formats:
        visible = key.split('##')[0]
        if visible not in table or '%' not in visible:
            continue
        value = table[visible]
        # Order matters: swapping %s and %d is unsafe even with equal counts.
        if PRINTF.findall(visible) != PRINTF.findall(value):
            errors.append(f'printf argument/order mismatch: {visible!r}')
        if '%' in PRINTF.sub('', value):
            errors.append(f'Unescaped percent in format: {visible!r}')
        checked_printf += 1
    formatter = string.Formatter()
    for key in fmt_formats:
        if key not in table:
            continue
        def fields(text):
            return [(field, spec, conversion) for _, field, spec, conversion in formatter.parse(text)
                    if field is not None]
        try:
            if fields(key) != fields(table[key]):
                errors.append(f'fmt argument/type mismatch: {key!r}')
        except ValueError:
            errors.append(f'Invalid fmt braces: {key!r}')
        checked_fmt += 1
    print(f'{len(table)} entries; {len(seen)} explicit display/data keys; '
          f'{len(audio)} audio and {len(cosmetics)} cosmetic labels; '
          f'{checked_printf} printf and {checked_fmt} fmt templates')
    for error in sorted(errors):
        print(error)
    return bool(errors)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
