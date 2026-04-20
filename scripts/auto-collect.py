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
    # 逆向/脱壳
    "逆向工程 脱壳 安全工具", "自动脱壳 skill 工具",
    "安卓逆向 frida unidbg", "ollvm 脱壳 逆向工具",
    "小程序逆向 安全工具", "x64dbg 脱壳 逆向",
    "VMP 脱壳 工具", "unidbg hook 逆向",
    # 爬虫/JS
    "JS逆向 爬虫 工具", "爬虫逆向 数据采集",
    "webdriver 检测 绕过", "appium 爬虫 逆向",
    # 渗透/漏洞
    "渗透测试 工具合集 安全", "漏洞利用 poc exp 工具",
    "内网渗透 红队工具", "Web安全 漏洞挖掘",
    "SQL注入 工具 合集", "XSS 漏洞 工具",
    # 审计/代码
    "代码审计 工具 合集", "Java 代码审计 工具",
    "PHP 代码审计 工具集", "Python 安全审计",
    # CTF/竞赛
    "CTF 工具 合集 逆向", "pwn 工具 二进制",
    "reverse CTF 工具集", "crypto CTF 工具",
    # 移动安全
    "Android 安全 工具 逆向", "iOS 安全 越狱 工具",
    "APK 反编译 工具", "frida 脚本 合集",
    # AI安全
    "AI安全 大模型安全 工具", "LLM 攻击 防御 工具",
    "prompt injection 工具", "AI 对抗样本 工具",
    # 社区/平台
    "吾爱破解 脱壳 逆向", "看雪论坛 逆向 安全",
    "FreeBuf 安全工具 合集", "安全客 工具 渗透",
    # 综合
    "网络安全 技能合集 awesome",
    "应急响应 取证分析",
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
    # 2026-04-20 新增：非安全类排除
    'material-3-skill', 'low-level-dev-skills', 'clarityfinance',
    'open-source-handbook', 'orchestkit', 'zeph',
    'aws_deepracer_worksheet', 'titanic-machine-learning',
    'python-basic-program', 'javascript-basic-program',
    'machine-learning-interview', 'a-online-quiz-site',
    'spellbook', 'skillarch', 'deepcamera', 'solana-claude',
    'athena', 'claw-ops-automation-suite',
    'agent-automation-toolkit', 'fuzzy-logic', 'don-cheli',
    'ai-best-practices', 'references', 'other-sources',
    'auto-songshu',
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

# 排除非安全相关的内容（关键词歧义、游戏剧情、电视剧等）
EXCLUDE_NON_SECURITY = [
    # 游戏/影视/小说类「渗透」
    '各人物结局', '电视剧', '电影', '小说', '剧情',
    # 百度知道/知乎问答（非工具/Skill）
    '有前途吗', '怎么学习', '应该准备', '以后打算', '作为过来人',
    '有什么方法', '怎么给', '怎么转换', '如何给',
    # 非技术内容
    'cadence', 'allegro', 'pcb设计',
    ' allegro skill', 'cadence skill',  # PCB 设计脚本，不是安全 skill
    # 教育/招生
    '招生简章', '报名时间', '学费',
    # 招聘
    '招聘 ', ' 岗位', '薪资', '月薪',
    # 法律法规
    '律师', '法律咨询', '判决书',
    # 非安全类（2026-04-20 新增）
    '逆向选择', '道德风险',  # 经济学概念
    '听歌', '音乐软件', '无损音质',
]

# GitHub 仓库必须命中的安全关键词（名称或描述）
GITHUB_MUST_HAVE_SECURITY = [
    'security', 'secure', 'vuln', 'vulnerability', '漏洞', '安全',
    'exploit', 'poc', 'payload', 'cve', 'cwe', 'owasp',
    'pentest', 'penetration', '渗透', 'hack', 'hacking', 'hacker',
    'attack', 'defense', 'defence', 'bypass',
    'malware', 'virus', 'trojan', 'ransomware', 'phishing',
    'audit', 'scanner', 'scan', 'nmap', 'nuclei', '代码审计',
    'sast', 'dast', 'static analysis', 'dynamic analysis',
    'reverse engineer', '逆向', 'decompile', 'disassemble',
    '脱壳', 'unpack', 'ghidra', 'ida pro', 'frida', 'unidbg',
    'hook', 'patch', 'crack', 'shellcode', '0day',
    'forensic', 'incident response', '应急响应', '取证',
    'threat hunt', 'threat intelligence', 'ioc',
    'ctf', 'capture the flag', 'pwn',
    'red team', 'blue team', 'purple team', '红队', '蓝队',
    'cobalt strike', 'metasploit', 'c2', 'active directory',
    'android security', 'ios security', '移动安全', 'apk', 'jailbreak',
    'xss', 'csrf', 'ssrf', 'sqli', 'sql injection', 'rce',
    'webshell', 'web security', 'lfi', 'rfi', 'xxe',
    'llm security', 'ai security', 'prompt injection', 'adversarial',
    'cryptography', 'crypto', 'encryption', '密码学', '加密',
    'osint', 'recon', 'bug bounty', 'waf', 'ids', 'ips', 'siem',
    'honeypot', 'sandbox', 'credential', 'privilege escalation',
    'lateral movement', 'supply chain', 'zero trust',
    'smart contract audit', 'solidity audit', 'blockchain security',
    'binary analysis', 'malware analysis', 'log analysis',
    'digital forensics', 'threat modeling',
]

# Skill 类型标识（中文文章至少要命中一个，才能被收录）
SKILL_SIGNALS = [
    'skill', '工具', '合集', 'awesome', 'collection', '框架',
    '自动化', '脚本', '插件', '模块', '平台',
    '教程', '指南', 'roadmap', '路线图', '清单',
    'exploit', 'poc', 'payload', 'scanner',
    '逆向', '脱壳', 'hook', 'frida', 'unidbg',
    '渗透测试', '漏洞利用', '代码审计', '应急响应',
    'pentest', 'audit', 'scanner', 'bypass',
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

    # ⚠️ 严格过滤：必须命中安全关键词，否则拒绝收录
    has_security = any(kw in text for kw in GITHUB_MUST_HAVE_SECURITY)
    if not has_security:
        return None, None  # 返回 None 表示不收录

    if any(k in text for k in ['audit', 'code review', '代码审计']): return '🔒 代码审计', None
    if any(k in text for k in ['pentest', 'penetration testing', 'bug bounty', '渗透']): return '⚔️ 渗透测试', None
    if any(k in text for k in ['reverse engineer', '逆向', 'malware analysis', 'ghidra', 'binary analysis', '脱壳']): return '🔍 逆向工程', None
    if any(k in text for k in ['ios', 'android', 'mobile security', 'apk', 'dvia', '移动安全']): return '📱 移动安全', None
    if any(k in text for k in ['ctf', 'capture the flag', 'pwn']): return '🏆 CTF 竞赛', None
    if any(k in text for k in ['threat', 'risk assessment', '威胁']): return '🎯 威胁建模', None
    if any(k in text for k in ['forensic', 'incident response', 'log analysis', '应急响应', '取证']): return '🚨 应急响应', None
    if any(k in text for k in ['payload', 'exploit', 'jndi', 'git dump', 'bypass']): return '🛡️ 安全工具', '漏洞利用'
    if any(k in text for k in ['red team', 'empire', 'covenant', 'active directory', '红队']): return '🛡️ 安全工具', '红队工具'
    if any(k in text for k in ['blue team', 'wazuh', 'velociraptor', 'grr', 'monitoring', '蓝队']): return '🛡️ 安全工具', '蓝队防御'
    if any(k in text for k in ['waf', 'safeline', 'modsecurity', 'fail2ban']): return '🛡️ 安全工具', 'WAF/防护'
    if any(k in text for k in ['scanner', 'nmap', 'nuclei', 'gobuster', 'hydra', 'xray', 'recon', '扫描']): return '🛡️ 安全工具', '安全扫描'
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
    """判断是否是网络安全/安全工具相关（严格模式）"""
    text = (title + ' ' + snippet).lower()

    # 第一关：排除非安全内容
    for kw in EXCLUDE_NON_SECURITY:
        if kw.lower() in text:
            return False

    # 第二关：必须命中安全关键词
    security_keywords = [
        '逆向', '脱壳', '漏洞', '安全', '审计', 'exploit',
        'poc', 'cve', 'ctf', 'revers', 'malware', 'binary',
        'frida', 'unidbg', 'ollvm', 'hook', 'patch', 'crack',
        'burp', 'metasploit', 'cobalt strike', 'nuclei', 'xray',
        '爬虫', 'js逆向', '小程序', '安卓', 'android', 'ios',
        '内网', '红队', '蓝队', '应急响应', '取证',
        '渗透测试', '漏洞利用', '代码审计', 'web安全',
        'sql注入', 'xss', 'csrf', 'ssrf',
        '逆向工程', '二进制', 'shellcode', '0day',
    ]
    has_security = any(kw in text for kw in security_keywords)
    if not has_security:
        return False

    # 第三关：「渗透」关键词需要额外检查，排除游戏/影视剧情
    if '渗透' in text and '渗透测试' not in text and '内网渗透' not in text:
        # 只有「渗透」二字太模糊，需要上下文确认是安全领域
        context_check = any(kw in text for kw in [
            '工具', '教程', '测试', '安全', '漏洞', '技术', '方法',
            'skill', '工具集', '合集', '框架',
        ])
        if not context_check:
            return False

    return True


def is_skill_article(title, snippet, url):
    """判断是否是真正的 Skill/工具/Skill-collection（不是普通问答）"""
    text = (title + ' ' + snippet).lower()
    url_lower = url.lower()

    # GitHub repo 直接认为是 skill
    if 'github.com' in url_lower:
        return True

    # 至少命中一个 Skill 信号词
    has_signal = any(kw in text for kw in SKILL_SIGNALS)
    if not has_signal:
        return False

    # 知乎问答：zhihu.com/question 路径 + 疑问句式 → 排除
    # 知乎专栏 zhuanlan.zhihu.com 的技术文章保留
    qa_patterns = [
        '有前途吗', '怎么学习', '应该准备', '以后打算',
        '作为过来人', '有什么方法', '怎么办', '好不好',
        '是什么', '为什么', '谁', '哪个', '如何最简单',
        '通俗地理解', '请教', '求推荐', '有哪些',
        '用什么', '哪家', '怎么选', '值得',
    ]
    is_qa = any(p in text for p in qa_patterns)
    is_question_url = 'zhihu.com/question' in url_lower or 'zhidao.baidu.com' in url_lower
    if is_qa and is_question_url:
        return False

    # 排除纯问答类（知乎问答、百度知道）
    # 如果是知乎/百度知道，标题要是问题形式 → 排除
    qa_patterns = [
        '有前途吗', '怎么学习', '应该准备', '以后打算',
        '作为过来人', '有什么方法', '怎么办', '好不好',
        '是什么', '为什么', '谁', '哪个',
    ]
    is_qa = any(p in text for p in qa_patterns)
    is_qa_platform = any(p in url_lower for p in ['zhihu.com/question', 'zhidao.baidu.com'])
    if is_qa and is_qa_platform:
        return False

    # 知乎文章（非问答）可以收录
    # 吾爱破解/看雪论坛的工具贴可以收录
    return True


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
            # 严格过滤：未命中安全关键词的条目直接跳过
            if cat is None:
                continue
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
            if not is_skill_article(title, snippet, url): continue

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
