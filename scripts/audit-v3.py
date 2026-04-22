#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SecSkills 第三轮清理 - 逐条审计所有条目
目标：只保留真正的 Skill/工具/框架/资源库
剔除：普通文章、论坛帖、问答页面、产品介绍
"""

import re

# ===== 真正的 Skill/工具 应该具备的特征 =====
# GitHub 仓库: 名称或描述包含 skill/tool/awesome/checklist/roadmap/kit 等
# 中文文章: 必须是「工具合集」「技能框架」「自动化脚本」等实操内容

# ===== 明确的非 Skill 模式 =====
# 这些条目应该被删除
REMOVE_PATTERNS = [
    # URL 模式 - 这些平台的内容 99% 不是 skill
    (r'zhihu\.com/tardis', '知乎问答/专栏页面'),
    (r'zhihu\.com/question', '知乎问答'),
    (r'zhihu\.com/.*art/\d', '知乎文章'),
    (r'zhidao\.baidu\.com', '百度知道'),
    (r'zone\.huoxian\.cn', '火线 Zone 社区文章'),
    (r'xz\.aliyun\.com', '先知社区文章'),
    (r'segmentfault\.com/a/', '思否文章'),
    (r'mdn\.org\.cn', 'MDN 文档（技术文档不是 skill）'),
    (r'info\.support\.huawei\.com', '华为支持文档'),
    (r'info-finder/encyclopedia', '华为百科'),
    (r'security\.360\.cn', '360 SRC 官网页面'),
    (r'bugku\.com', 'Bugku CTF 论坛首页'),
    (r'wilesangh\.github\.io', '个人 GitHub Pages'),
    
    # 吾爱破解论坛帖子（不是 skill 本身）
    (r'52pojie\.cn/thread-', '吾爱破解帖子（非工具/Skill）'),
    (r'52pojie\.cn/forum\.php', '吾爱破解论坛板块'),
    
    # 微信公众号文章（除非明确是工具发布）
    (r'mp\.weixin\.qq\.com', '微信公众号文章'),
    
    # 名称模式
    (r'零基础.*入门', '入门教程文章'),
    (r'看完这一篇', '教程文章'),
    (r'非常详细.*入门', '教程文章'),
    (r'从.*到精通', '教程文章'),
    (r'什么是.*？', '科普文章'),
    (r'入门教程', '入门教程'),
    (r'学习路线', '学习路线文章'),
    (r'学习笔记', '学习笔记（非工具）'),
    (r'解题思路', '解题文章'),
    (r'怎么防止', '科普问答'),
    (r'如何防止', '科普问答'),
    (r'有前途吗', '问答'),
    (r'怎么入门', '问答'),
    (r'怎么学习', '问答'),
    (r'应该准备', '问答'),
]

# ===== 保留的 skill 特征 =====
KEEP_SIGNALS = [
    'skill', 'tool', '工具', '合集', 'awesome', 'collection',
    'checklist', 'roadmap', 'framework', '框架',
    '自动化', '脚本', '插件', '模块', '平台',
    '指南', '清单', 'exploit', 'poc', 'payload',
    'scanner', '逆向', '脱壳', 'hook', 'frida',
    'unidbg', '渗透测试', '漏洞利用', '代码审计',
    '应急响应', 'pentest', 'audit', 'bypass',
    'checklist', 'workbook', 'challenge', 'training',
]

def audit_entry(name, desc, source, url):
    """返回 (True, reason) 表示应删除"""
    text = (name + ' ' + desc + ' ' + url).lower()
    
    # 第一关：URL 模式匹配
    for pattern, reason in REMOVE_PATTERNS:
        if re.search(pattern, url, re.IGNORECASE):
            return True, reason
    
    # 第二关：名称模式匹配
    for pattern, reason in REMOVE_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True, reason
    
    return False, ''


def main():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, 'README.md')
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    current_cat = None
    current_sub = None
    to_remove = []
    all_entries = []
    
    for i, line in enumerate(lines):
        cat_match = re.match(r'^### (.+)', line.strip())
        if cat_match:
            current_cat = cat_match.group(1).strip()
            current_sub = None
            continue
        sub_match = re.match(r'^#### (.+)', line.strip())
        if sub_match:
            current_sub = sub_match.group(1).strip()
            continue
        
        match = re.match(
            r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[(.+?)\]\(([^)]+)\)\s*\|',
            line
        )
        if not match:
            continue
            
        name = match.group(1)
        desc = match.group(2)
        source = match.group(3)
        url = match.group(4)
        
        entry = {
            'line': i + 1,
            'name': name,
            'desc': desc,
            'source': source,
            'url': url,
            'category': current_cat,
            'subcategory': current_sub,
        }
        all_entries.append(entry)
        
        should_remove, reason = audit_entry(name, desc, source, url)
        if should_remove:
            to_remove.append((entry, reason))
    
    # 输出结果
    print(f"总条目: {len(all_entries)}")
    print(f"应删除: {len(to_remove)}")
    print(f"应保留: {len(all_entries) - len(to_remove)}")
    print(f"\n{'='*100}")
    
    # 按原因分类
    by_reason = {}
    for entry, reason in to_remove:
        by_reason.setdefault(reason, []).append(entry)
    
    for reason, entries in sorted(by_reason.items(), key=lambda x: -len(x[1])):
        print(f"\n🗑️  {reason} ({len(entries)} 条)")
        print(f"{'─'*80}")
        for e in entries:
            print(f"  [{e['category']}] {e['name'][:60]}  ←  行 {e['line']}")
    
    # 输出要保留但值得检查的条目
    print(f"\n\n{'='*100}")
    print("⚠️  可疑条目（非 GitHub 来源，建议人工复核）:")
    print(f"{'─'*80}")
    
    kept_non_gh = []
    for entry in all_entries:
        should_remove, _ = audit_entry(entry['name'], entry['desc'], entry['source'], entry['url'])
        if not should_remove and 'github.com' not in entry['url'].lower():
            kept_non_gh.append(entry)
    
    for e in kept_non_gh:
        print(f"  [{e['category']}] {e['name'][:50]}  ←  [{e['source']}] {e['url'][:80]}")

if __name__ == '__main__':
    main()
