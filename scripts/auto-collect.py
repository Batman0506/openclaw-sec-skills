#!/usr/bin/env python3
# -*- coding utf-8 -*-
"""
OpenClaw SecSkills 自动化搜集脚本 v2
1. GitHub API 搜索英文安全 skill
2. Bing 搜索中文安全 skill（微信/看雪/掘金/吾爱破解等）
3. 合并去重，更新 README
"""

import json
import re
import os
import time
from datetime import datetime
from urllib.request import urlopen, Request, ProxyHandler, build_opener
from urllib.parse import quote, urlencode

# 代理 opener（仅用于 Bing 等外网搜索，GitHub API 直连）
PROXY = 'http://127.0.0.1:7890'
_web_opener = None

def _get_web_opener():
    global _web_opener
    if _web_opener is None:
        proxy_handler = ProxyHandler({'http': PROXY, 'https': PROXY})
        _web_opener = build_opener(proxy_handler)
    return _web_opener

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

# ====== GitHub 英文关键词 ======
GITHUB_KEYWORDS = [
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

# ====== Bing 中文关键词 ======
BING_KEYWORDS = [
    "逆向工程 脱壳 安全工具", "自动脱壳 skill 工具",
    "安卓逆向 frida unidbg", "JS逆向 爬虫 工具",
    "渗透测试 工具合集 安全", "代码审计 工具 合集",
    "CTF 工具 合集 逆向", "漏洞利用 poc exp 工具",
    "内网渗透 红队工具", "应急响应 取证分析",
    "AI安全 大模型安全 工具", "网络安全 技能合集 awesome",
    "吾爱破解 脱壳 逆向", "看雪论坛 逆向 安全",
    "ollvm 脱壳 逆向工具", "小程序逆向 安全工具",
]

# ====== 排除列表 ======
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
}

EXCLUDE_DESC = [
    'according to all known laws of aviation',
    'skip to content',
    'all gists back to github',
    'instantly share code',
    'search\u2026 all gists',
]

EXCLUDE_CN = [
    '关注回复', '点击阅读原文', '点击蓝色字', '长按识别二维码',
    '本文转载自', '如有侵权请联系删除', '免责声明',
    '点击上方', '关注我', '点赞', '在看', '转发',
    '拼多多', '淘宝', '京东', '天猫',
    '盐选', '会员', '付费',
]

EXISTING_REPOS = set()
EXISTING_TITLES = set()
EXISTING_URLS = set()
ALL_ENTRIES = []


# ============================================================
# README 解析
# ============================================================
def parse_readme(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    details_match = re.search(r'<details[^>]*>(.*?)</details>', content, re.DOTALL)
    if not details_match:
        return content, ""

    details_body = details_match.group(1)
    header = content[:details_match.start()]
    tail = content[details_match.end():]
    tail = re.sub(r'\n+## 🆕 新收录 \(.*?\)\n+.*?(?=\n## |\Z)', '', tail, flags=re.DOTALL)

    current_cat = None
    current_sub = None
    for line in details_body.split('\n'):
        cat_match = re.match(r'^### (.+)', line.strip())
        if cat_match:
            current_cat = cat_match.group(1).strip()
            current_sub = None
            continue
        sub_match = re.match(r'^#### (.+)', line.strip())
        if sub_match:
            current_sub = sub_match.group(1).strip()
            continue

        # GitHub 链接行
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
                EXISTING_TITLES.add(name.lower())
                EXISTING_URLS.add(url)
                ALL_ENTRIES.append({
                    'name': name, 'desc': desc, 'url': url,
                    'category': current_cat, 'subcategory': current_sub,
                    'stars': 0, 'source': 'github',
                })
                continue

        # 中文文章行
        cn_match = re.match(
            r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[(.+?)\]\((https?://[^)]+)\)\s*\|',
            line
        )
        if cn_match and current_cat:
            name = cn_match.group(1)
            desc = cn_match.group(2)
            source_label = cn_match.group(3)
            url = cn_match.group(4)
            EXISTING_TITLES.add(name.lower())
            EXISTING_URLS.add(url)
            ALL_ENTRIES.append({
                'name': name, 'desc': desc, 'url': url,
                'category': current_cat, 'subcategory': current_sub,
                'stars': 0, 'source': source_label,
            })

    return header, tail


# ============================================================
# GitHub API 搜索
# ============================================================
def github_search(query, per_page=10, max_retries=5):
    url = f"https://api.github.com/search/repositories?q={quote(query)}&sort=stars&order=desc&per_page={per_page}"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_TOKEN}' if GITHUB_TOKEN.startswith('github_pat_') else f'token {GITHUB_TOKEN}'
    for attempt in range(1, max_retries + 1):
        try:
            req = Request(url, headers=headers)
            response = urlopen(req, timeout=15)
            remaining = response.headers.get('X-RateLimit-Remaining', 'unknown')
            reset_ts = response.headers.get('X-RateLimit-Reset', '0')
            if remaining == '0':
                wait = max(int(reset_ts) - int(time.time()) + 5, 10)
                print(f"    ⏳ 速率限制耗尽，等待 {wait} 秒...")
                time.sleep(wait)
                continue
            return json.loads(response.read().decode('utf-8')).get('items', [])
        except Exception as e:
            err_str = str(e)
            if '403' in err_str or '429' in err_str:
                wait = 15 * attempt
                print(f"    ⏳ HTTP {err_str[:50]}，等待 {wait} 秒后重试 ({attempt}/{max_retries})...")
                time.sleep(wait)
                continue
            elif '401' in err_str:
                print(f"    ✗ Token 无效")
                return []
            else:
                print(f"    ✗ {err_str[:100]}")
                return []
    return []


def classify_github(desc, name):
    text = (desc + ' ' + name).lower()
    if any(k in text for k in ['audit', 'code review']): return '🔒 代码审计', None
    if any(k in text for k in ['pentest', 'penetration testing', 'bug bounty']): return '⚔️ 渗透测试', None
    if any(k in text for k in ['reverse engineering', 'malware analysis', 'ghidra', 'binary analysis']): return '🔍 逆向工程', None
    if any(k in text for k in ['ios', 'android', 'mobile security', 'apk', 'dvia']): return '📱 移动安全', None
    if any(k in text for k in ['ctf', 'capture the flag']): return '🏆 CTF 竞赛', None
    if any(k in text for k in ['threat', 'risk assessment']): return '🎯 威胁建模', None
    if any(k in text for k in ['forensic', 'incident response', 'log analysis']): return '🚨 应急响应', None
    if any(k in text for k in ['payload', 'exploit', 'jndi', 'git dump', 'bypass']): return '🛡️ 安全工具', '漏洞利用'
    if any(k in text for k in ['red team', 'empire', 'covenant', 'active directory']): return '🛡️ 安全工具', '红队工具'
    if any(k in text for k in ['blue team', 'wazuh', 'velociraptor', 'grr', 'monitoring']): return '🛡️ 安全工具', '蓝队防御'
    if any(k in text for k in ['waf', 'safeline', 'modsecurity', 'fail2ban']): return '🛡️ 安全工具', 'WAF/防护'
    if any(k in text for k in ['scanner', 'nmap', 'nuclei', 'gobuster', 'hydra', 'xray', 'recon']): return '🛡️ 安全工具', '安全扫描'
    if any(k in text for k in ['osint', 'sherlock', 'spiderfoot', 'amass', 'subfinder', 'maltego', 'harvester']): return '🛡️ 安全工具', '信息收集/OSINT'
    return '🛡️ 安全工具', None


# ============================================================
# Bing HTML 搜索（中文安全内容）
# ============================================================
def bing_search(query, max_results=10):
    """通过 Bing 搜索中文安全内容（走 Mihomo 代理）"""
    url = f"https://www.bing.com/search?q={quote(query)}&count={max_results}&mkt=zh-CN"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    results = []
    for attempt in range(1, 4):
        try:
            req = Request(url, headers=headers)
            response = _get_web_opener().open(req, timeout=15)
            html = response.read().decode('utf-8')

            items = re.findall(r'class="b_algo"(.*?)(?=class="b_algo"|$)', html, re.DOTALL)
            for item in items[:max_results]:
                h2 = re.search(r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', item, re.DOTALL)
                p = re.search(r'<p[^>]*>(.*?)</p>', item, re.DOTALL)
                if h2:
                    title = re.sub(r'<[^>]+>', '', h2.group(2)).strip()
                    raw_url = h2.group(1).replace('&amp;', '&')
                    snippet = ''
                    if p:
                        snippet = re.sub(r'<[^>]+>', '', p.group(1)).strip()
                    results.append({
                        'title': title, 'snippet': snippet[:150], 'url': raw_url,
                    })
            if results:
                break
        except Exception as e:
            wait = 5 * attempt
            print(f"    ⏳ Bing 搜索失败: {str(e)[:80]}，等待 {wait} 秒...")
            time.sleep(wait)
    return results


def is_cn_security(title, snippet):
    text = (title + ' ' + snippet).lower()
    keywords = [
        '逆向', '脱壳', '渗透', '漏洞', '安全', '审计', 'exploit',
        'poc', 'cve', 'ctf', 'revers', 'malware', 'binary',
        'frida', 'unidbg', 'ollvm', 'hook', 'patch', 'crack',
        'burp', 'metasploit', 'cobalt strike', 'nuclei', 'xray',
        '爬虫', 'js逆向', '小程序', '安卓', 'android', 'ios',
        '内网', '红队', '蓝队', '应急响应', '取证',
        'skill', '工具', 'collection', '合集', 'awesome',
        '破解', 'exploit', 'payload', 'shellcode',
    ]
    return any(kw in text for kw in keywords)


def is_garbage(title, snippet):
    text = title + ' ' + snippet
    return any(kw in text for kw in EXCLUDE_CN)


def extract_source(url):
    u = url.lower()
    if 'mp.weixin.qq.com' in u: return '微信公众号'
    if 'kanxue.com' in u or 'pediy.com' in u: return '看雪论坛'
    if 'juejin.cn' in u or 'juejin.im' in u: return '掘金'
    if 'csdn.net' in u: return 'CSDN'
    if 'github.com' in u: return 'GitHub'
    if 'bilibili.com' in u: return 'B站'
    if 'zhihu.com' in u: return '知乎'
    if 'freebuf.com' in u: return 'FreeBuf'
    if 'anquanke.com' in u: return '安全客'
    if 't00ls.com' in u: return 'T00ls'
    if '52pojie.cn' in u: return '吾爱破解'
    return '其他'


def cn_classify(title, snippet):
    text = (title + ' ' + snippet).lower()
    if any(k in text for k in ['逆向', 'reverse', '脱壳', 'unpack', 'ollvm', 'unidbg', 'frida', 'hook', '破解']):
        return '🔍 逆向工程', '脱壳/逆向'
    if any(k in text for k in ['爬虫', 'spider', 'scraping', '数据采集']):
        return '🔍 逆向工程', '爬虫/数据采集'
    if any(k in text for k in ['渗透', 'pentest', 'exploit', 'poc', 'cve', '漏洞利用']):
        return '⚔️ 渗透测试', None
    if any(k in text for k in ['审计', 'audit', 'code review']):
        return '🔒 代码审计', None
    if any(k in text for k in ['ctf', 'capture the flag']):
        return '🏆 CTF 竞赛', None
    if any(k in text for k in ['安卓', 'android', 'apk']):
        return '📱 移动安全', 'Android'
    if any(k in text for k in ['ios', 'iphone']):
        return '📱 移动安全', 'iOS'
    if any(k in text for k in ['内网', '红队', 'cobalt', 'empire']):
        return '🛡️ 安全工具', '红队工具'
    if any(k in text for k in ['应急响应', '取证', 'forensic']):
        return '🚨 应急响应', None
    if any(k in text for k in ['ai安全', 'ai security', '大模型', 'llm']):
        return '🛡️ 安全工具', 'AI安全'
    return '🛡️ 安全工具', '其他'


# ============================================================
# 搜索执行
# ============================================================
def search_github():
    print(f"\n📡 GitHub 搜索 {len(GITHUB_KEYWORDS)} 个关键词...")
    new = []
    for i, kw in enumerate(GITHUB_KEYWORDS):
        print(f"  [{i+1}/{len(GITHUB_KEYWORDS)}] {kw}")
        for repo in github_search(kw):
            full_name = repo.get('full_name', '').lower()
            if full_name in EXISTING_REPOS: continue
            name = repo.get('name', '')
            if name.lower() in EXCLUDE_NAMES: continue
            if any(k.lower() in name.lower() for k in EXCLUDE_NAMES): continue
            if repo.get('stargazers_count', 0) < 10: continue
            if repo.get('fork', False): continue
            desc_raw = repo.get('description', '') or ''
            if any(k.lower() in desc_raw.lower() for k in EXCLUDE_DESC): continue
            cat, sub = classify_github(desc_raw, name)
            entry = {
                'name': name, 'desc': desc_raw[:120],
                'url': repo.get('html_url', ''),
                'category': cat, 'subcategory': sub,
                'stars': repo.get('stargazers_count', 0), 'source': 'github',
            }
            new.append(entry)
            EXISTING_REPOS.add(full_name)
        time.sleep(2.2)
    print(f"  GitHub 发现 {len(new)} 个新 Skills")
    return new


def search_bing():
    print(f"\n🔍 Bing 中文搜索 {len(BING_KEYWORDS)} 个关键词...")
    new = []
    for i, kw in enumerate(BING_KEYWORDS):
        print(f"  [{i+1}/{len(BING_KEYWORDS)}] {kw}")
        results = bing_search(kw, max_results=8)
        for r in results:
            title = r['title']
            snippet = r['snippet']
            url = r['url']

            if title.lower() in EXISTING_TITLES: continue
            if url in EXISTING_URLS: continue
            if is_garbage(title, snippet): continue
            if not is_cn_security(title, snippet): continue

            source = extract_source(url)
            cat, sub = cn_classify(title, snippet)
            entry = {
                'name': title,
                'desc': snippet[:120] if snippet else f'来自 {source} 的中文安全资源',
                'url': url, 'category': cat, 'subcategory': sub,
                'stars': 0, 'source': source,
            }
            new.append(entry)
            EXISTING_TITLES.add(title.lower())
            EXISTING_URLS.add(url)
        time.sleep(1.5)
    print(f"  Bing 发现 {len(new)} 个新资源")
    return new


# ============================================================
# README 生成
# ============================================================
def regenerate_readme(header, tail, new_skills):
    for s in new_skills:
        ALL_ENTRIES.append(s)

    by_cat = {}
    for e in ALL_ENTRIES:
        cat, sub = e['category'], e.get('subcategory')
        if cat not in by_cat:
            by_cat[cat] = {'_main': [], '_subs': {}}
        if sub:
            if sub not in by_cat[cat]['_subs']:
                by_cat[cat]['_subs'][sub] = []
            by_cat[cat]['_subs'][sub].append(e)
        else:
            by_cat[cat]['_main'].append(e)

    sub_order = ['脱壳/逆向', '爬虫/数据采集', '漏洞利用', '红队工具', '蓝队防御',
                 '安全检查', '安全扫描', 'WAF/防护', '信息收集/OSINT', 'AI安全', '其他']
    cat_order = [
        '🔒 代码审计', '⚔️ 渗透测试', '🔍 逆向工程',
        '🏆 CTF 竞赛', '🎯 威胁建模', '📱 移动安全',
        '🚨 应急响应', '🛡️ 安全工具',
    ]
    cat_desc = {
        '🔒 代码审计': '白盒代码安全审计，覆盖 Java/PHP/Python/智能合约等',
        '⚔️ 渗透测试': '自动化渗透测试、漏洞挖掘、Bug Bounty',
        '🔍 逆向工程': '二进制分析、恶意样本分析、JS 逆向、脱壳',
        '🏆 CTF 竞赛': 'CTF 解题技巧、工具使用、漏洞挖掘',
        '🎯 威胁建模': '安全风险评估、威胁分析、合规检查',
        '📱 移动安全': 'Android/iOS 安全分析、漏洞挖掘',
        '🚨 应急响应': '安全事件响应、取证分析、日志分析',
        '🛡️ 安全工具': '扫描器、漏洞利用、红蓝对抗工具、AI 安全',
    }

    lines = []
    for cat in cat_order:
        if cat not in by_cat: continue
        lines.append(f'\n### {cat}\n')
        lines.append(f'\n> {cat_desc.get(cat, "")}\n')
        data = by_cat[cat]
        if data['_main']:
            data['_main'].sort(key=lambda x: -x.get('stars', 0))
            lines.append('\n| Skill | 描述 | 来源 |')
            lines.append('|-------|------|------|')
            for e in data['_main']:
                src = e.get('source', 'github')
                lines.append(f'| **{e["name"]}** | {e["desc"]} | [{src}]({e["url"]}) |')
        for sub in sub_order:
            if sub not in data['_subs']: continue
            lines.append(f'\n#### {sub}')
            items = data['_subs'][sub]
            items.sort(key=lambda x: -x.get('stars', 0))
            lines.append('\n| Skill | 描述 | 来源 |')
            lines.append('|-------|------|------|')
            for e in items:
                src = e.get('source', 'github')
                lines.append(f'| **{e["name"]}** | {e["desc"]} | [{src}]({e["url"]}) |')

    details = '<details open>\n' + '\n'.join(lines) + '\n\n</details>'
    return header + details + '\n\n' + tail.lstrip()


# ============================================================
# 主流程
# ============================================================
def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, 'README.md')

    print("=" * 60)
    print("OpenClaw SecSkills 自动化搜集 v2")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    header, tail = parse_readme(readme_path)
    print(f"已解析 {len(ALL_ENTRIES)} 个已有条目，{len(EXISTING_REPOS)} 个 GitHub 仓库")

    github_new = search_github()
    bing_new = search_bing()

    all_new = github_new + bing_new
    content = regenerate_readme(header, tail, all_new)
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)

    total = len(ALL_ENTRIES)
    print(f"\n✅ README 已更新，共 {total} 个 Skills（本次新增 {len(all_new)}：GitHub {len(github_new)} + 中文 {len(bing_new)}）")
    print("=" * 60)


if __name__ == '__main__':
    main()
