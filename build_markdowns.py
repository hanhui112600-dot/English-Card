# -*- coding: utf-8 -*-
import json
import re
import os
import data_2007
import data_2008
import data_2009
import data_2010

cards_2010_t1 = data_2010.cards_2010_t1
print(f"Loaded {len(cards_2010_t1)} cards for 2010 Text 1")

# 汇总所有卡片
all_2007 = data_2007.cards_2007_t1 + data_2007.cards_2007_t2 + data_2007.cards_2007_t3 + data_2007.cards_2007_t4
all_2008 = data_2008.cards_2008_t1 + data_2008.cards_2008_t2
all_2009 = data_2009.cards_2009_t1 + data_2009.cards_2009_t2 + data_2009.cards_2009_t3 + data_2009.cards_2009_t4
all_2010 = cards_2010_t1 + data_2010.cards_2010_t2 + data_2010.cards_2010_t3 + data_2010.cards_2010_t4

total_cards = all_2007 + all_2008 + all_2009 + all_2010
print(f"Total cards across all years: {len(total_cards)}")

# 辅助函数：生成 Markdown 文件内容
def generate_markdown(year, texts_dict, pending_texts=None):
    if pending_texts is None:
        pending_texts = []
    
    total_count = sum(len(cards) for cards in texts_dict.values())
    
    lines = []
    lines.append(f"# {year} 年考研英语真题精读知识点卡片库")
    lines.append("")
    lines.append("> 每年划分 4 篇精读阅读（Text 1 ~ Text 4）。")
    lines.append("> 本笔记沉淀手写黑笔复盘考点，配齐真题原句语境，支持在手机应用端【按篇复习】或【整年通刷】。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 目录索引")
    
    chinese_nums = ["一", "二", "三", "四"]
    for i in range(1, 5):
        t_key = f"Text {i}"
        c_num = chinese_nums[i-1]
        if t_key in texts_dict and len(texts_dict[t_key]) > 0:
            count = len(texts_dict[t_key])
            anchor = f"{c_num.lower()}-{t_key.lower().replace(' ', '-')}"
            lines.append(f"- [{c_num}、 {t_key}（共 {count} 处考点 · 已录入）](#{anchor})")
            lines.append("  - [1. 熟词生义与词性活用](#1-熟词生义与词性活用)")
            lines.append("  - [2. 固定短语与搭配用法](#2-固定短语与搭配用法)")
            lines.append("  - [3. 考研核心重点词汇](#3-考研核心重点词汇)")
            lines.append("  - [4. 核心句型与语法批注](#4-核心句型与语法批注)")
        else:
            lines.append(f"- [{c_num}、 {t_key}（待录入 · 待提供笔记图片）](#{c_num.lower()}-{t_key.lower().replace(' ', '-')})")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # 篇章分类输出
    cat_order = [
        ("熟词生义", "1. 熟词生义与词性活用"),
        ("固定短语", "2. 固定短语与搭配用法"),
        ("核心词汇", "3. 考研核心重点词汇"),
        ("句型语法", "4. 核心句型与语法批注")
    ]
    
    for i in range(1, 5):
        t_key = f"Text {i}"
        c_num = chinese_nums[i-1]
        if t_key in texts_dict and len(texts_dict[t_key]) > 0:
            cards = texts_dict[t_key]
            lines.append(f"## {c_num}、 {t_key}（共 {len(cards)} 处考点 · 已录入）")
            lines.append("")
            
            # 分类展示
            idx = 1
            for cat_name, cat_title in cat_order:
                cat_cards = [c for c in cards if c["category"] == cat_name]
                if not cat_cards:
                    continue
                lines.append(f"### {cat_title}")
                lines.append("")
                for c in cat_cards:
                    num_str = f"{idx:02d}"
                    word_display = c["word"]
                    lines.append(f"> [!NOTE] {num_str}. {word_display}")
                    lines.append(f"> **【核心释义】**：{c['def']}")
                    if c.get("noteTag"):
                        lines.append(f"> **【考点讲解】**：=={c['noteTag']}== ")
                    lines.append("> **真题例句**：")
                    # 将 <mark>...</mark> 转为 **...**
                    sentence_md = c["sentence"].replace("<mark>", "**").replace("</mark>", "**")
                    lines.append(f"> {sentence_md}")
                    lines.append(f"> **真题译文**：{c['translation']}")
                    lines.append("")
                    idx += 1
                lines.append("---")
                lines.append("")
        else:
            lines.append(f"## {c_num}、 {t_key}（待录入）")
            lines.append(f"*待拍照录入 {year} {t_key} 手写笔记知识点后自动填充...*")
            lines.append("")
            lines.append("---")
            lines.append("")
            
    return "\n".join(lines)

# 生成 2007
md_2007 = generate_markdown(2007, {
    "Text 1": data_2007.cards_2007_t1,
    "Text 2": data_2007.cards_2007_t2,
    "Text 3": data_2007.cards_2007_t3,
    "Text 4": data_2007.cards_2007_t4
})
with open('2007年真题知识点卡片库.md', 'w', encoding='utf-8') as f:
    f.write(md_2007)
print("Written 2007年真题知识点卡片库.md")

# 生成 2008
md_2008 = generate_markdown(2008, {
    "Text 1": data_2008.cards_2008_t1,
    "Text 2": data_2008.cards_2008_t2
}, pending_texts=["Text 3", "Text 4"])
with open('2008年真题知识点卡片库.md', 'w', encoding='utf-8') as f:
    f.write(md_2008)
print("Written 2008年真题知识点卡片库.md")

# 生成 2009
md_2009 = generate_markdown(2009, {
    "Text 1": data_2009.cards_2009_t1,
    "Text 2": data_2009.cards_2009_t2,
    "Text 3": data_2009.cards_2009_t3,
    "Text 4": data_2009.cards_2009_t4
})
with open('2009年真题知识点卡片库.md', 'w', encoding='utf-8') as f:
    f.write(md_2009)
print("Written 2009年真题知识点卡片库.md")

# 生成 2010
md_2010 = generate_markdown(2010, {
    "Text 1": cards_2010_t1,
    "Text 2": data_2010.cards_2010_t2,
    "Text 3": data_2010.cards_2010_t3,
    "Text 4": data_2010.cards_2010_t4
})
with open('2010年真题知识点卡片库.md', 'w', encoding='utf-8') as f:
    f.write(md_2010)
print("Written 2010年真题知识点卡片库.md")

print("All 4 Markdown files generated successfully!")
