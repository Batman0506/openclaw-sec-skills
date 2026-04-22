#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SecSkills README 清理脚本 - 删除所有非 skill 条目
"""
import re
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
readme_path = os.path.join(base_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

REMOVE_PATTERNS = [
    (r'zhihu\.com/tardis', '知乎'),
    (r'zhihu\.com/question', '知乎问答'),
    (r'52pojie\.cn/thread-', '吾爱帖子'),
    (r'52pojie\.cn/forum\.php', '吾爱板块'),
    (r'zone\.huoxian\.cn', '火线Zone'),
    (r'mp\.weixin\.qq\.com', '微信文章'),
    (r'info\.support\.huawei\.com', '华为支持'),
    (r'xz\.aliyun\.com', '先知社区'),
    (r'segmentfault\.com/a/', '思否文章'),
    (r'mdn\.org\.cn', 'MDN文档'),
    (r'security\.360\.cn', '360SRC'),
    (r'bugku\.com', 'Bugku论坛'),
    (r'wilesangh\.github\.io', '个人Pages'),
]

new_lines = []
removed = 0

for line in lines:
    match = re.match(
        r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[(.+?)\]\(([^)]+)\)\s*\|',
        line
    )
    if match:
        url = match.group(4)
        name = match.group(1)
        should_remove = False
        reason = ''
        for pattern, r in REMOVE_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                should_remove = True
                reason = r
                break
        if should_remove:
            removed += 1
            continue
    
    new_lines.append(line)

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"已删除 {removed} 条非 skill 条目")
