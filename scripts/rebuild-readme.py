#!/usr/bin/env python3
"""
重建 SecSkills README - 清理所有批次插入的混乱格式
将所有 skill 条目提取后，按分类重新组织，插入正确位置
"""
import re, os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
readme_path = os.path.join(base_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取所有 skill 条目
entries = []
current_cat = None
current_sub = None

for line in content.split('\n'):
    cat_match = re.match(r'^### (.+)', line.strip())
    if cat_match:
        current_cat = cat_match.group(1).strip()
        current_sub = None
        continue
    sub_match = re.match(r'^#### (.+)', line.strip())
    if sub_match:
        current_sub = sub_match.group(1).strip()
        continue

    # 匹配表格行
    m = re.match(r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[GitHub\]\(([^)]+)\)\s*\|', line)
    if m and current_cat:
        name = m.group(1)
        desc = m.group(2)
        url = m.group(3)
        entries.append({
            'name': name, 'desc': desc, 'url': url,
            'category': current_cat, 'subcategory': current_sub
        })

# 去重（同名同 URL 只保留一条）
seen = set()
unique_entries = []
for e in entries:
    key = (e['name'].lower(), e['url'])
    if key not in seen:
        seen.add(key)
        unique_entries.append(e)

print(f"提取到 {len(entries)} 条，去重后 {len(unique_entries)} 条")

# 按分类组织
by_cat = {}
for e in unique_entries:
    cat, sub = e['category'], e.get('subcategory')
    if cat not in by_cat:
        by_cat[cat] = {'main': [], 'subs': {}}
    if sub:
        if sub not in by_cat[cat]['subs']:
            by_cat[cat]['subs'][sub] = []
        by_cat[cat]['subs'][sub].append(e)
    else:
        by_cat[cat]['main'].append(e)

# 打印统计
for cat, data in sorted(by_cat.items()):
    total = len(data['main']) + sum(len(v) for v in data['subs'].values())
    print(f"  {cat}: {total} 条 (主表 {len(data['main'])} + 子表 {total - len(data['main'])})")

# 保存提取结果
import json
with open('/tmp/sec_skills_extracted.json', 'w') as f:
    json.dump(unique_entries, f, ensure_ascii=False)

print("\n提取完成，已保存到 /tmp/sec_skills_extracted.json")
