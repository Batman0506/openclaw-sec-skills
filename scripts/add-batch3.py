#!/usr/bin/env python3
import re, os

BATCH3 = [
    ('jalaalrd/full-stack-audit', '90-point full-stack audit skill for websites and web apps. Catches security holes, accessibility issues', '🔒 代码审计', None, 24),
    ('svdwalt007/Best-LwM2M-Agentic-Skills', 'Worlds most comprehensive OMA LwM2M (IoT) expert skill for Claude', '🛡️ 安全工具', 'AI安全', 6),
]

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
readme_path = os.path.join(base_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

marker = '## 🆕 新收录'
idx = content.find(marker)
if idx == -1:
    print("ERROR: 找不到新收录标记")
    exit(1)

lines = []
lines.append('\n### 🔒 代码审计\n')
for name, desc, cat, sub, stars in BATCH3:
    if cat == '🔒 代码审计':
        short_name = name.split('/')[-1]
        lines.append(f'| **{short_name}** | {desc} | [GitHub](https://github.com/{name}) |')

lines.append('\n### 🛡️ 安全工具\n')
lines.append('\n#### AI安全\n')
for name, desc, cat, sub, stars in BATCH3:
    if cat == '🛡️ 安全工具':
        short_name = name.split('/')[-1]
        lines.append(f'| **{short_name}** | {desc} | [GitHub](https://github.com/{name}) |')

new_section = '\n'.join(lines)
new_content = content[:idx] + new_section + '\n' + content[idx:]

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ 已新增 {len(BATCH3)} 个 skills")
