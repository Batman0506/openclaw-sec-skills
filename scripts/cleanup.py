#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SecSkills README 清理脚本
1. 逐行扫描 README，识别非网络安全相关的条目
2. 删除明显无关的条目
3. 修复重复条目
4. 更新 README
"""

import re
from datetime import datetime

# ====== 必须保留的安全关键词（至少命中一个） ======
# GitHub 条目：名称或描述中必须命中至少一个
SECURITY_KEYWORDS = [
    # 核心安全
    'security', 'secure', '安全',
    'vuln', 'vulnerability', '漏洞',
    'exploit', 'poc', 'payload',
    'cve', 'cwe', 'owasp',
    'pentest', 'penetration', '渗透',
    'hack', 'hacking', 'hacker',
    'attack', 'defense', 'defence',
    'bypass', ' evasion',
    'malware', 'virus', 'trojan', 'ransomware',
    'phishing', 'social engineering',
    # 审计/分析
    'audit', 'scanner', 'scan', 'nmap', 'nuclei',
    'code review', '代码审计',
    'static analysis', 'sast', 'dast', 'iast',
    'dynamic analysis',
    # 逆向/二进制
    'reverse engineer', 'binary analysis', '逆向',
    'decompile', 'disassemble', '脱壳', 'unpack',
    'ghidra', 'ida pro', 'radare', 'binary ninja',
    'frida', 'unidbg', 'hook', 'patch', 'crack',
    'shellcode', '0day',
    # 应急响应/取证
    'forensic', 'incident response', '应急响应',
    '取证', 'log analysis', '日志分析',
    'threat hunt', 'threat intelligence',
    'ioc', 'indicator of compromise',
    # CTF/竞赛
    'ctf', 'capture the flag',
    'pwn', 'crypto ctf',
    # 红队/蓝队
    'red team', 'blue team', 'purple team',
    '红队', '蓝队', '紫队',
    'cobalt strike', 'metasploit', 'impacket',
    'c2', 'command and control',
    'active directory', 'kerberos',
    # 移动安全
    'android security', 'ios security', '移动安全',
    'apk', 'ipa', 'jailbreak', '越狱',
    'frida', 'xposed', 'magisk',
    # Web安全
    'xss', 'csrf', 'ssrf', 'sqli', 'sql injection',
    'rce', 'remote code execution',
    'lfi', 'rfi', 'xxe',
    'webshell', 'web security',
    # AI安全
    'llm security', 'ai security', 'prompt injection',
    'model security', 'adversarial',
    # 加密/密码学
    'cryptography', 'crypto', 'encryption',
    '密码学', '加密', '解密',
    # 其他安全
    'osint', 'recon', 'reconnaissance', '侦察',
    'bug bounty', 'responsible disclosure',
    'waf', 'ids', 'ips', 'siem',
    'honeypot', '蜜罐',
    'sandbox', '沙箱',
    'credential', 'password', 'credential stuffing',
    'privilege escalation', '提权',
    'lateral movement', '横向移动',
    'supply chain', '供应链安全',
    'zero trust', '零信任',
    'rbac', 'abac', 'access control',
]

# ====== 明确排除的关键词（命中即删除） ======
EXCLUDE_PATTERNS = [
    # UI/设计
    'material design', 'md3', 'ui component', 'design token', 'theming', 'responsive layout',
    # 编程语言基础
    'python basic program', 'javascript basic', 'basic program',
    # 机器学习/数据科学
    'machine learning', 'ml interview', 'titanic', 'data science', 'kaggle',
    'recommendation system', 'fuzzy logic', 'research topic',
    # AI Agent（非安全）
    'ai development toolkit', '103 skills', '36 agents', '172 hooks',
    'oh-my-', 'plugin framework', 'supercharge claude',
    # 金融
    'financial analysis', 'finance agent',
    # 教育/通用
    'open source handbook', 'open source projects for all skill',
    'online quiz', 'quiz system',
    # AWS
    'deepracer', 'reinforcement learning',
    # 其他
    'according to all known laws', 'skip to content',
    'song', 'music', '听歌', '无损音质',
    '逆向选择', '道德风险',  # 经济学概念
    'cadence', 'allegro', 'pcb设计',
]

# ====== 明确排除的仓库名 ======
EXCLUDE_REPOS = {
    'material-3-skill',
    'low-level-dev-skills',
    'clarityfinance',
    'open-source-handbook',
    'orchestkit',
    'zeph',
    'aws_deepracer_worksheet',
    'fuzzy-logic-based-recommendation-system-for-research-topic-in-the-final-year',
    'titanic-machine-learning-from-disaster',
    'python-basic-programs',
    'javascript-basic-program',
    'machine-learning-interview-preparation',
    'a-online-quiz-site',
    'references',  # AI textbook references
    'other-sources',  # Academic paper references
    'deepcamera',  # AI Camera platform
    'skillarch',
    'athena',  # Clean code development, not security
    'solana-claude',  # Solana builder configs
    'spellbook',  # General AI coding skills
    'claw-ops-automation-suite',
    'agent-automation-toolkit',
}

# ====== 需要删除的中文文章 ======
EXCLUDE_CN_TITLES = [
    '什么是逆向选择和道德风险？',
    '10款免费听歌软件',
    '如何学习软件逆向工程？',
]


def is_security_related(name, desc, url=''):
    """判断条目是否是网络安全相关"""
    text = (name + ' ' + desc + ' ' + url).lower()

    # 第一关：检查排除列表
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in text:
            return False, pattern

    # 第二关：检查排除仓库名
    if name.lower() in EXCLUDE_REPOS:
        return False, 'excluded repo'

    # 第三关：必须命中至少一个安全关键词
    has_security = any(kw in text for kw in SECURITY_KEYWORDS)
    if not has_security:
        return False, 'no security keyword'

    return True, None


def clean_readme(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 details 部分
    details_match = re.search(r'(<details[^>]*>.*?</details>)', content, re.DOTALL)
    if not details_match:
        print("❌ 未找到 <details> 标签")
        return

    details = details_match.group(1)
    header = content[:details_match.start()]
    tail = content[details_match.end():]

    lines = details.split('\n')
    new_lines = []
    removed = []
    seen_urls = set()
    seen_names_lower = set()
    removed_count = 0
    duplicate_count = 0

    for line in lines:
        # 保留分类标题和表头
        if line.strip().startswith('### ') or line.strip().startswith('#### '):
            new_lines.append(line)
            continue
        if line.strip().startswith('> '):
            new_lines.append(line)
            continue
        if line.strip().startswith('| Skill |') or line.strip().startswith('|-------|'):
            new_lines.append(line)
            continue
        if line.strip() == '':
            new_lines.append(line)
            continue
        if line.strip().startswith('<details') or line.strip().startswith('</details>'):
            new_lines.append(line)
            continue

        # 检查数据行
        github_match = re.match(
            r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|',
            line
        )
        if github_match:
            name = github_match.group(1)
            desc = github_match.group(2)
            source = github_match.group(3)
            url = github_match.group(4)

            # 去重检查
            url_key = url.lower().rstrip('/')
            name_key = name.lower().strip()

            if url_key in seen_urls:
                duplicate_count += 1
                removed.append(f"  [重复] {name} ({source})")
                removed_count += 1
                continue
            if name_key in seen_names_lower and source.lower() == 'github':
                duplicate_count += 1
                removed.append(f"  [重名] {name} ({source})")
                removed_count += 1
                continue

            seen_urls.add(url_key)
            if source.lower() == 'github':
                seen_names_lower.add(name_key)

            # 安全检查
            is_sec, reason = is_security_related(name, desc, url)
            if not is_sec:
                removed.append(f"  [非安全] {name} — 原因: {reason}")
                removed_count += 1
                continue

            new_lines.append(line)
            continue

        # 其他行（中文文章等）也做类似处理
        cn_match = re.match(
            r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[(.+?)\]\((https?://[^)]+)\)\s*\|',
            line
        )
        if cn_match:
            name = cn_match.group(1)
            desc = cn_match.group(2)
            source = cn_match.group(3)
            url = cn_match.group(4)

            url_key = url.lower().rstrip('/')
            if url_key in seen_urls:
                duplicate_count += 1
                removed.append(f"  [重复] {name} ({source})")
                removed_count += 1
                continue
            seen_urls.add(url_key)

            # 排除特定中文标题
            if any(excl in name for excl in EXCLUDE_CN_TITLES):
                removed.append(f"  [非安全] {name}")
                removed_count += 1
                continue

            new_lines.append(line)
            continue

        # 保留其他行
        new_lines.append(line)

    # 写入清理后的内容
    new_details = '\n'.join(new_lines)
    new_content = header + new_details + '\n\n' + tail.lstrip()

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"\n✅ 清理完成!")
    print(f"   删除非安全条目: {removed_count - duplicate_count}")
    print(f"   删除重复条目: {duplicate_count}")
    print(f"   总计删除: {removed_count}")

    if removed:
        print(f"\n📋 删除清单:")
        for r in removed:
            print(r)


if __name__ == '__main__':
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, 'README.md')
    clean_readme(readme_path)
