#!/usr/bin/env python3
import re, os

BATCH2 = [
    ('kaivyy/perseus', 'AI-powered security assessment SKILLS for your codebase. Multi-language (JS, Go, Python, Java)', '🔒 代码审计', None, 65),
    ('OEN-Tech/incident-report-skill', 'Claude Code skill: Taiwan cybersecurity incident report generator', '🚨 应急响应', None, 60),
    ('eth0izzle/security-skills', 'A collection of Claude Code skills that help security teams stay secure', '🛡️ 安全工具', '安全检查', 38),
    ('briiirussell/cybersecurity-skills', 'Cybersecurity skills for AI coding agents (Claude Code, Cursor, Codex)', '🛡️ 安全工具', 'AI安全', 10),
    ('Njones17/AI-agent-master-cyber-skills-list', 'Comprehensive cybersecurity skill pack for AI coding agents — 741 skills', '🛡️ 安全工具', 'AI安全', 7),
    ('Orizon-eu/claude-code-pentest', '6 Claude Code skills that automate the entire pentest lifecycle. From recon to exploitation', '⚔️ 渗透测试', None, 6),
    ('h4vzz/awesome-ai-agent-skills', '70+ ready-to-use, platform-agnostic AI agent skills', '🛡️ 安全工具', 'AI安全', 7),
    ('EthanYolo01/Awesome-OpenClaw', 'A carefully curated list of awesome OpenClaw resources', '🛡️ 安全工具', '其他', 152),
]

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
readme_path = os.path.join(base_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 "## 🆕 新收录" 的位置，在它之前插入新内容
marker = '## 🆕 新收录'
idx = content.find(marker)
if idx == -1:
    print("ERROR: 找不到新收录标记")
    exit(1)

lines = []
lines.append('### 🔒 代码审计\n')
lines.append(f'| **perseus** | AI-powered security assessment SKILLS for codebase. Multi-language | [GitHub](https://github.com/kaivyy/perseus) |')
lines.append('\n### ⚔️ 渗透测试\n')
lines.append(f'| **claude-code-pentest** | 6 skills that automate the entire pentest lifecycle. From recon to exploitation | [GitHub](https://github.com/Orizon-eu/claude-code-pentest) |')
lines.append('\n### 🚨 应急响应\n')
lines.append(f'| **incident-report-skill** | Taiwan cybersecurity incident report generator | [GitHub](https://github.com/OEN-Tech/incident-report-skill) |')
lines.append('\n### 🛡️ 安全工具\n')
for name, desc, cat, sub, stars in BATCH2:
    if cat == '🛡️ 安全工具':
        short_name = name.split('/')[-1]
        lines.append(f'| **{short_name}** | {desc} | [GitHub](https://github.com/{name}) |')

new_section = '\n'.join(lines)
new_content = content[:idx] + new_section + '\n' + content[idx:]

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"✅ 已新增 8 个 skills 到新收录区域")
