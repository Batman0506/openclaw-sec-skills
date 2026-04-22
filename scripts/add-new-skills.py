#!/usr/bin/env python3
import json, re, os

NEW_SKILLS = [
    ('mukul97/Anthropic-Cybersecurity-Skills', '754 structured cybersecurity skills for AI agents, mapped to MITRE ATT&CK, NIST, OWASP', '⚔️ 渗透测试', None, 5519),
    ('sangrokjung/claude-forge', 'Supercharge Claude Code with 11 AI agents, 36 commands & 15 skills', '⚔️ 渗透测试', None, 659),
    ('AgentSecOps/SecOpsAgentKit', 'Security operations toolkit for AI coding agents. 25+ skills for CVE research, exploit dev, threat intel', '🚨 应急响应', None, 123),
    ('d0gesec/pownie', 'Agent harness for offensive security. Plugin for Claude Code packed with skills, memory, rules', '⚔️ 渗透测试', None, 21),
    ('Jumbo-WJB/pentest-skills', '自动化渗透 agent skills', '⚔️ 渗透测试', None, 19),
    ('jph4cks/redhound-arsenal', '76 AI-agent security skills for Kali Linux tools — pentest, red team, forensics', '🛡️ 安全工具', '安全扫描', 2),
    ('chaubes/trivy-security-agent-skill', 'AI-powered Trivy security scanning skill for Claude Code', '🔒 代码审计', None, 0),
    ('Stacksheild/sentinelai', 'Security scanner, cost tracker, and model router for the AI ecosystem', '🔒 代码审计', None, 1),
    ('friday-james/dependency-scanner', 'Claude Code skill that scans npm/pip dependencies for vulnerabilities', '🔒 代码审计', None, 0),
    ('vgrichina/re-skill', 'Claude Code skill for reverse engineering retro games — disassemble, annotate, explore', '🔍 逆向工程', None, 93),
    ('NikolasMarkou/epistemic-deconstructor', 'Claude skill for reverse engineering systems', '🔍 逆向工程', None, 20),
    ('incogbyte/android-reverse-engineering-claude-skill', 'Decompile Android APK, XAPK, AAB, DEX, JAR using jadx', '🔍 逆向工程', None, 17),
    ('caiovicentino/apple-silicon-internals', 'Reverse engineering toolkit for Apple Silicon private APIs. 55+ frameworks', '🔍 逆向工程', None, 13),
    ('incogbyte/iOS-reverse-engineering-claude-skill', 'Claude Code skill for extracting, analyzing, reverse engineering iOS apps', '🔍 逆向工程', None, 8),
    ('Masriyan/Claude-Code-CyberSecurity-Skill', 'Comprehensive collection of 15 Claude Code Skills for cybersecurity', '🛡️ 安全工具', 'AI安全', 6),
    ('kadenzipfel/scv-scan', 'Claude Code skill that scans Solidity codebases for security vulnerabilities', '🛡️ 安全工具', '安全扫描', 98),
    ('Fuzzdkk/dfir-skills', 'DFIR/SOC skillset for Claude Code — memory forensics, log analysis, network forensics', '🚨 应急响应', None, 2),
]

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
readme_path = os.path.join(base_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

existing = set()
for m in re.finditer(r'github\.com/([^/]+/[^\s|)]+)', content):
    existing.add(m.group(1).lower())

new_ones = [s for s in NEW_SKILLS if s[0].lower() not in existing]

print(f"待新增 {len(new_ones)} 个 skills（过滤掉 {len(NEW_SKILLS) - len(new_ones)} 个已存在）:")
for s in new_ones:
    name, desc, cat, sub, stars = s
    short_name = name.split('/')[-1]
    print(f"  [{cat}] {short_name} (⭐{stars}) → {desc[:60]}")

# 写入 README
# 找到 <details open> 的结束位置
details_end = content.find('</details>')
if details_end == -1:
    print("ERROR: 找不到 </details>")
    exit(1)

# 构建新条目
by_cat = {}
for name, desc, cat, sub, stars in new_ones:
    short_name = name.split('/')[-1]
    if cat not in by_cat:
        by_cat[cat] = {'main': [], 'subs': {}}
    if sub:
        if sub not in by_cat[cat]['subs']:
            by_cat[cat]['subs'][sub] = []
        by_cat[cat]['subs'][sub].append((short_name, desc, name, stars))
    else:
        by_cat[cat]['main'].append((short_name, desc, name, stars))

# 插入位置：在现有内容的最后 </details> 之前
insert_lines = []
insert_lines.append('\n## 🆕 新收录 (2026-04-22)\n')
insert_lines.append('> 本轮清理删除了 59 条非 skill 文章/论坛帖，补充了以下高质量项目\n')

for cat, data in sorted(by_cat.items()):
    insert_lines.append(f'\n### {cat}\n')
    if data['main']:
        for short_name, desc, full_name, stars in sorted(data['main'], key=lambda x: -x[3]):
            insert_lines.append(f'| **{short_name}** | {desc} | [GitHub](https://github.com/{full_name}) |')
    for sub, items in data['subs'].items():
        insert_lines.append(f'\n#### {sub}\n')
        for short_name, desc, full_name, stars in sorted(items, key=lambda x: -x[3]):
            insert_lines.append(f'| **{short_name}** | {desc} | [GitHub](https://github.com/{full_name}) |')

new_content = content[:details_end] + '\n' + '\n'.join(insert_lines) + '\n' + content[details_end:]

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"\n✅ 已更新 README，新增 {len(new_ones)} 个 skills")
