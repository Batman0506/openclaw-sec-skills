#!/usr/bin/env python3
"""
完整重建 SecSkills README
1. 提取所有 skill 条目（不管来源标签大小写）
2. 去掉「🆕 新收录」区域的重复项
3. 按分类重新组织，确保每个分类有完整表头和分隔线
4. 新 skills 直接插入对应分类表格
"""
import re, os, json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
readme_path = os.path.join(base_dir, 'README.md')

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 提取 header（<details open> 之前）
header = content.split('<details')[0]

# 提取 footer（</details> 之后）
footer_match = re.search(r'</details>(.*)', content, re.DOTALL)
footer = footer_match.group(1) if footer_match else ''

# 提取所有 skill 条目（在 <details> 区域内）
details_match = re.search(r'<details[^>]*>(.*?)</details>', content, re.DOTALL)
if not details_match:
    print("ERROR: 找不到 <details>")
    exit(1)

details_content = details_match.group(1)
entries = []
current_cat = None
current_sub = None

for line in details_content.split('\n'):
    # 跳过空行、描述行、表头行
    if not line.strip() or line.strip().startswith('>') or line.strip().startswith('| Skill'):
        continue
    if line.strip() == '|-------|------|------|':
        continue

    cat_match = re.match(r'^### (.+)', line.strip())
    if cat_match:
        current_cat = cat_match.group(1).strip()
        current_sub = None
        continue
    sub_match = re.match(r'^#### (.+)', line.strip())
    if sub_match:
        current_sub = sub_match.group(1).strip()
        continue

    # 匹配所有表格行（[GitHub]/[github]/[其他]/[知乎] 等）
    m = re.match(r'\|\s+\*\*(.+?)\*\*\s*\|\s*(.*?)\s*\|\s*\[(.+?)\]\(([^)]+)\)\s*\|', line)
    if m and current_cat:
        name = m.group(1)
        desc = m.group(2)
        source = m.group(3)
        url = m.group(4)
        
        # 跳过「新收录」区域的条目（避免重复）
        # 新收录区域没有子分类且 source 都是 github
        # 我们通过后续去重处理
        
        entries.append({
            'name': name, 'desc': desc, 'url': url,
            'category': current_cat, 'subcategory': current_sub,
            'source': source.lower()
        })

# 去重：同名+同 URL 只保留一条
seen = set()
unique_entries = []
for e in entries:
    key = (e['name'].lower(), e['url'])
    if key not in seen:
        seen.add(key)
        unique_entries.append(e)

print(f"提取到 {len(entries)} 条，去重后 {len(unique_entries)} 条")

# 按分类组织
cat_order = [
    '🔒 代码审计', '⚔️ 渗透测试', '🔍 逆向工程',
    '🏆 CTF 竞赛', '🎯 威胁建模', '📱 移动安全',
    '🚨 应急响应', '🛡️ 安全工具',
]

sub_order = ['脱壳/逆向', '爬虫/数据采集', '漏洞利用', '红队工具', '蓝队防御',
             '安全检查', '安全扫描', 'WAF/防护', '信息收集/OSINT', 'AI安全', '其他']

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

# 生成新的 <details> 内容
lines = []
for cat in cat_order:
    if cat not in by_cat:
        continue
    data = by_cat[cat]
    
    lines.append(f'\n### {cat}\n')
    lines.append(f'> {cat_desc.get(cat, "")}\n')
    
    # 主表
    if data['main']:
        lines.append('| Skill | 描述 | 来源 |')
        lines.append('|-------|------|------|')
        for e in data['main']:
            src = e['source'].title() if e['source'] != 'github' else 'github'
            lines.append(f'| **{e["name"]}** | {e["desc"]} | [{src}]({e["url"]}) |')
    
    # 子表
    for sub in sub_order:
        if sub not in data['subs']:
            continue
        items = data['subs'][sub]
        lines.append(f'\n#### {sub}')
        lines.append('| Skill | 描述 | 来源 |')
        lines.append('|-------|------|------|')
        for e in items:
            src = e['source'].title() if e['source'] != 'github' else 'github'
            lines.append(f'| **{e["name"]}** | {e["desc"]} | [{src}]({e["url"]}) |')

details_body = '\n'.join(lines)

# 组装完整 README
new_content = header.strip() + '\n\n<details open>\n' + details_body + '\n\n</details>' + footer

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

# 统计
total = sum(len(d['main']) + sum(len(v) for v in d['subs'].values()) for d in by_cat.values())
print(f"\n✅ README 已重建，共 {total} 个 Skills")
for cat in cat_order:
    if cat in by_cat:
        d = by_cat[cat]
        cnt = len(d['main']) + sum(len(v) for v in d['subs'].values())
        print(f"  {cat}: {cnt}")
