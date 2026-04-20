#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SecSkills 第二轮清理 - 逐条审计所有条目
找出仍然不是网络安全类的条目
"""

import re

# 明确的非安全条目（名称或描述中包含）
NOT_SECURITY = [
    # 名称关键词匹配
    ('agile_v_skills', 'AI工程敏捷框架，不是安全'),
    ('ai-best-practices-skills', 'AI最佳实践，不是安全'),
    ('摩尔浓度', '化学计算工具'),
    ('molarity-calculator', '化学计算工具'),
    ('Xbox.*S.*X', 'Xbox游戏机指南，不是安全（XSS是缩写误导）'),
    ('2025年入手XSX', 'Xbox游戏机购买指南'),
    ('XSX,XSS指南', 'Xbox游戏机指南'),
    ('360安全龙虾', '360 AI客户端产品，不是安全工具'),
    ('龙虾卫士', '360产品页面'),
    ('360官网', '360产品官网'),
    ('FreeBuf.*知乎', '知乎专栏页面，不是具体技能'),
    ('有没有什么web安全', '知乎问答推荐平台'),
    ('研究帮手', '化学计算工具'),
    ('Amino Acids', '氨基酸转换器，化学'),
    ('retro game', '复古游戏逆向，偏游戏不是安全'),
    ('retro games', '复古游戏逆向'),
    ('KotlinCrackMaster', 'CrackMe教育项目，但属于逆向学习'),
    # 知乎问答（非工具/文章）
    ('如何最简单', '知乎问答'),
    ('通俗地理解', '知乎问答'),
    ('用哪种大模型进行ctf', '百度知道问答'),
]

# 排除平台（知乎问答页、百度知道）
EXCLUDE_URL_PATTERNS = [
    'zhihu.com/question',  # 知乎问答（非技术文章）
    'zhidao.baidu.com',     # 百度知道
]

# 需要人工判断的可疑条目
SUSPICIOUS = [
    're-skill',          # retro games
    'CEH-Assessments',    # 认证评估
    'TimeCod',           # KotlinCrackMaster
    'agile_v_skills',     # AI工程
    'ai-best-practices-skills',
]


def audit_readme(readme_path):
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    to_remove = []

    for i, line in enumerate(lines):
        # 检查数据行
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
        text = (name + ' ' + desc + ' ' + url).lower()

        # 检查 URL 排除模式
        for pattern in EXCLUDE_URL_PATTERNS:
            if pattern in url.lower():
                to_remove.append((i + 1, name, source, f'排除平台: {pattern}'))
                break
        else:
            # 检查非安全关键词
            for keyword, reason in NOT_SECURITY:
                if re.search(keyword, text, re.IGNORECASE):
                    to_remove.append((i + 1, name, source, reason))
                    break

    return to_remove


if __name__ == '__main__':
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    readme_path = os.path.join(base_dir, 'README.md')
    results = audit_readme(readme_path)

    print(f"🔍 发现 {len(results)} 个需要删除的条目:\n")
    for line_num, name, source, reason in results:
        print(f"  行 {line_num:4d} | {name[:50]:50s} | [{source}] | {reason}")
