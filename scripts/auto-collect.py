#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw SecSkills 自动化搜集脚本
自动搜索 GitHub 上的网络安全相关 Skills 并更新 README
"""

import json
import re
import os
import time
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.parse import quote

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

SEARCH_KEYWORDS = [
    "code audit skill", "java audit skill", "php audit skill",
    "smart contract audit", "solidity audit skill",
    "pentest skill", "penetration testing skill", "bug bounty skill",
    "vulnerability assessment skill",
    "red team skill", "blue team skill",
    "reverse engineering skill", "malware analysis skill",
    "binary analysis skill", "ghidra skill",
    "mobile security skill", "android security skill", "ios security skill",
    "incident response skill", "digital forensics skill", "log analysis skill",
    "security scanner skill", "vulnerability scanner skill",
    "ctf skill", "capture the flag skill",
    "threat intelligence skill", "threat hunting skill",
    "owasp skill", "mitre attack skill",
    "llm security skill", "ai security skill",
]

EXCLUDE_NAMES = {
    'china-dictatorship', 'beemovie', 'bee-movie', 'bee movie',
    'comp_sci_sem', 'in-class-project', 'design-motion',
    'avoid-ai-writing', 'ai-marketing-claude', 'ai-legal-claude',
    'claude-ads', 'seo-geo', 'seo-audit', 'vibe-security',
    'ultraship', 'everything-claude-code', 'quivr', 'gitleaks',
    'db-gpt', 'chatgpt_system_prompt', 'hexstrike-ai',
    'superagent', 'flask-appbuilder', 'textattack', 'metorial',
    'osmedeus', 'purplellama', 'anthropic-cybersecurity-skills',
    'ai-infra-guard', 'cyberstrikeai', 'ciso-assistant-community',
    'awesome_gpt_super_prompting', 'cai',
    'redesigned-pancake', 'torrents',
    'known-laws-of-aviation', 'dvia-v2', 'dvia',
    'seo-geo', 'seo-audit',
}

# 排除描述中包含这些词的非相关仓库
EXCLUDE_DESC = [
    'according to all known laws of aviation',
    'skip to content',
    'all gists back to github',
    'instantly share code',
    'search\u2026 all gists',
]

EXISTING_REPOS = set()
ALL_ENTRIES = []  # list of dicts with: name, desc, url, category, subcategory, stars


def parse_readme(readme_path):
    """解析 README，提取所有已有条目"""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    details_match = re.search(r'<details[^>]*>(.*?)</details>', content, re.DOTALL)
    if not details_match:
        return content, ""

    details_body = details_match.group(1)
    header = content[:details_match.start()]
    tail = content[details_match.end():]

    # 清理 tail 中的 🆕 新收录段落
    tail = re.sub(r'\n+## 🆕 新收录 \(.*?\)\n+.*?(?=\n## |\Z)', '', tail, flags=re.DOTALL)

    current_cat = None
    current_sub = None
    for line in details_body.split('\n'):
        # 匹配 ### 分类标题
        cat_match = re.match(r'^### (.+)', line.strip())
        if cat_match:
            current_cat = cat_match.group(1).strip()
            current_sub = None
            continue

        # 匹配 #### 子分类
        sub_match = re.match(r'^#### (.+)', line.strip())
        if sub_match:
            current_sub = sub_match.group(1).strip()
            continue

        # 匹配表格行
        row_match = re.match(
            r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[GitHub\]\(([^)]+)\)\s*\|',
            line
        )
        if row_match and current_cat:
            name = row_match.group(1)
            desc = row_match.group(2)
            url = row_match.group(3)
            repo_match = re.search(r'github\.com/([^/]+/[^/]+)', url)
            if repo_match:
                EXISTING_REPOS.add(repo_match.group(1).lower())
                ALL_ENTRIES.append({
                    'name': name,
                    'desc': desc,
                    'url': url,
                    'category': current_cat,
                    'subcategory': current_sub,
                    'stars': 0,
                })

    return header, tail


def github_search(query, per_page=10):
    url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc&per_page={per_page}"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    try:
        req = Request(url, headers=headers)
        response = urlopen(req, timeout=10)
        return json.loads(response.read().decode('utf-8')).get('items', [])
    except Exception as e:
        print(f"    ✗ {e}")
        return []


def classify(desc, name):
    """分类"""
    text = (desc + ' ' + name).lower()
    if any(k in text for k in ['audit', 'code review']):
        return '🔒 代码审计', None
    if any(k in text for k in ['pentest', 'penetration testing', 'bug bounty']):
        return '⚔️ 渗透测试', None
    if any(k in text for k in ['reverse engineering', 'malware analysis', 'ghidra', 'binary analysis']):
        return '🔍 逆向工程', None
    if any(k in text for k in ['ios', 'android', 'mobile security', 'apk', 'dvia', 'damn vulnerable ios']):
        return '📱 移动安全', None
    if any(k in text for k in ['ctf', 'capture the flag']):
        return '🏆 CTF 竞赛', None
    if any(k in text for k in ['threat', 'risk assessment']):
        return '🎯 威胁建模', None
    if any(k in text for k in ['forensic', 'incident response', 'log analysis']):
        return '🚨 应急响应', None
    # 安全工具子分类
    if any(k in text for k in ['payload', 'exploit', 'jndi', 'git dump', 'bypass']):
        return '🛡️ 安全工具', '漏洞利用'
    if any(k in text for k in ['red team', 'empire', 'covenant', 'active directory', 'ad attack', 'windows exploit']):
        return '🛡️ 安全工具', '红队工具'
    if any(k in text for k in ['blue team', 'wazuh', 'velociraptor', 'grr', 'monitoring', 'default cred']):
        return '🛡️ 安全工具', '蓝队防御'
    if any(k in text for k in ['waf', 'safeline', 'modsecurity', 'fail2ban']):
        return '🛡️ 安全工具', 'WAF/防护'
    if any(k in text for k in ['scanner', 'nmap', 'nuclei', 'gobuster', 'hydra', 'xray', 'cherrybomb', 'recon']):
        return '🛡️ 安全工具', '安全扫描'
    if any(k in text for k in ['osint', 'sherlock', 'spiderfoot', 'amass', 'subfinder', 'maltego', 'harvester', 'reconftw']):
        return '🛡️ 安全工具', '信息收集/OSINT'
    if any(k in text for k in ['skill audit', 'skillguard', 'skill-audit', 'security check', 'security audit']):
        return '🛡️ 安全工具', '安全检查'
    return '🛡️ 安全工具', None


def search_all():
    print(f"搜索 {len(SEARCH_KEYWORDS)} 个关键词...")
    new = []
    for i, kw in enumerate(SEARCH_KEYWORDS):
        print(f"  [{i+1}/{len(SEARCH_KEYWORDS)}] {kw}")
        for repo in github_search(kw):
            full_name = repo.get('full_name', '').lower()
            if full_name in EXISTING_REPOS:
                continue
            name = repo.get('name', '')
            name_lower = name.lower()
            if name_lower in EXCLUDE_NAMES:
                continue
            skip_name = False
            for kw in EXCLUDE_NAMES:
                if kw.lower() in name_lower:
                    skip_name = True
                    break
            if skip_name:
                continue
            if repo.get('stargazers_count', 0) < 10:
                continue
            if repo.get('fork', False):
                continue
            desc_raw = repo.get('description', '') or ''
            desc_lower = desc_raw.lower()
            skip = False
            for kw in EXCLUDE_DESC:
                if kw.lower() in desc_lower:
                    skip = True
                    break
            if skip:
                continue
            desc = desc_raw[:120]
            url = repo.get('html_url', '')
            cat, sub = classify(desc, name)
            entry = {
                'name': name,
                'desc': desc,
                'url': url,
                'category': cat,
                'subcategory': sub,
                'stars': repo.get('stargazers_count', 0),
            }
            new.append(entry)
            EXISTING_REPOS.add(full_name)
        time.sleep(0.3)
    print(f"发现 {len(new)} 个新 Skills")
    return new


def regenerate_readme(header, tail, new_skills):
    """重新生成 details 区块"""
    # 把新技能合并到 ALL_ENTRIES
    for s in new_skills:
        ALL_ENTRIES.append(s)

    # 按分类/子分类分组
    by_cat = {}  # cat -> {None: [main], sub: [sub]}
    for e in ALL_ENTRIES:
        cat = e['category']
        sub = e.get('subcategory')
        if cat not in by_cat:
            by_cat[cat] = {'_main': [], '_subs': {}}
        if sub:
            if sub not in by_cat[cat]['_subs']:
                by_cat[cat]['_subs'][sub] = []
            by_cat[cat]['_subs'][sub].append(e)
        else:
            by_cat[cat]['_main'].append(e)

    # 安全工具的子分类顺序
    sub_order = ['漏洞利用', '红队工具', '蓝队防御', '安全检查', '安全扫描', 'WAF/防护', '信息收集/OSINT']
    # 分类顺序
    cat_order = [
        '🔒 代码审计', '⚔️ 渗透测试', '🔍 逆向工程',
        '🏆 CTF 竞赛', '🎯 威胁建模', '📱 移动安全',
        '🚨 应急响应', '🛡️ 安全工具',
    ]
    cat_desc = {
        '🔒 代码审计': '白盒代码安全审计，覆盖 Java/PHP/Python/智能合约等',
        '⚔️ 渗透测试': '自动化渗透测试、漏洞挖掘、Bug Bounty',
        '🔍 逆向工程': '二进制分析、恶意样本分析、JS 逆向',
        '🏆 CTF 竞赛': 'CTF 解题技巧、工具使用、漏洞挖掘',
        '🎯 威胁建模': '安全风险评估、威胁分析、合规检查',
        '📱 移动安全': 'Android/iOS 安全分析、漏洞挖掘',
        '🚨 应急响应': '安全事件响应、取证分析、日志分析',
        '🛡️ 安全工具': '扫描器、漏洞利用、红蓝对抗工具',
    }

    lines = []
    for cat in cat_order:
        if cat not in by_cat:
            continue
        lines.append(f'\n### {cat}\n')
        lines.append(f'\n> {cat_desc.get(cat, "")}\n')

        data = by_cat[cat]
        # 主表格
        if data['_main']:
            data['_main'].sort(key=lambda x: -x.get('stars', 0))
            lines.append('\n| Skill | 描述 | 仓库 |')
            lines.append('|-------|------|------|')
            for e in data['_main']:
                lines.append(f'| **{e["name"]}** | {e["desc"]} | [GitHub]({e["url"]}) |')

        # 子分类
        for sub in sub_order:
            if sub not in data['_subs']:
                continue
            lines.append(f'\n#### {sub}')
            items = data['_subs'][sub]
            items.sort(key=lambda x: -x.get('stars', 0))
            lines.append('\n| Skill | 描述 | 仓库 |')
            lines.append('|-------|------|------|')
            for e in items:
                lines.append(f'| **{e["name"]}** | {e["desc"]} | [GitHub]({e["url"]}) |')

    details = '<details open>\n' + '\n'.join(lines) + '\n\n</details>'
    return header + details + '\n\n' + tail.lstrip()


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, 'README.md')

    print("=" * 60)
    print("OpenClaw SecSkills 自动化搜集")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    header, tail = parse_readme(readme_path)
    print(f"已解析 {len(ALL_ENTRIES)} 个已有条目，{len(EXISTING_REPOS)} 个仓库")

    new = search_all()

    content = regenerate_readme(header, tail, new)
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    total = len(ALL_ENTRIES)
    print(f"\nREADME 已更新，共 {total} 个 Skills（新增 {len(new)}）")
    print("=" * 60)


if __name__ == '__main__':
    main()
