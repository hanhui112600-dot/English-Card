# -*- coding: utf-8 -*-
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import json
import re
import os
import glob
import importlib

with open('考研英语刷题卡.html', 'r', encoding='utf-8') as f:
    orig_html = f.read()

# 动态聚合所有卡片数据
data_files = sorted(glob.glob("data_20*.py"))
all_cards = []
for df in data_files:
    mod_name = os.path.splitext(os.path.basename(df))[0]
    mod = importlib.import_module(mod_name)
    for attr in sorted(dir(mod)):
        if attr.startswith("cards_"):
            val = getattr(mod, attr)
            if isinstance(val, list):
                all_cards.extend(val)
print(f"Total cards ready for HTML: {len(all_cards)}")

# 格式化 ALL_CARDS 的 JavaScript 代码
cards_js_str = "    const ALL_CARDS = " + json.dumps(all_cards, ensure_ascii=False, indent=6) + ";"

pattern = r'const ALL_CARDS = \[.*?\];'
if not re.search(pattern, orig_html, re.DOTALL):
    raise Exception("Pattern for ALL_CARDS not found in HTML")

new_html = re.sub(pattern, cards_js_str, orig_html, flags=re.DOTALL)
print("Replaced ALL_CARDS in HTML")

# 1. 修复 Cloze blank 语境挖空构建逻辑
cloze_old = """      // 语境挖空句子构建
      const blankSentence = card.sentencePlain.replace(new RegExp(card.word.replace(/[.*+?^${}()|[\]\\]/g, '\\\\$&'), 'gi'), `<span class="cloze-blank">【 ? 】</span>`);
      document.getElementById('frontClozeSentence').innerHTML = blankSentence;"""

cloze_new = """      // 语境挖空句子构建 (优先基于 <mark> 标签精准挖空，处理变形及附注词)
      let blankSentence = card.sentence ? card.sentence.replace(/<mark>[\\s\\S]*?<\\/mark>/gi, '<span class="cloze-blank">【 ? 】</span>') : '';
      if (blankSentence === card.sentence && card.sentencePlain && card.word) {
        const cleanWord = card.word.replace(/\\(.*?\\)/g, '').trim();
        if (cleanWord) {
          blankSentence = card.sentencePlain.replace(new RegExp(cleanWord.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&'), 'gi'), '<span class="cloze-blank">【 ? 】</span>');
        }
      }
      document.getElementById('frontClozeSentence').innerHTML = blankSentence;"""

if cloze_old in new_html:
    new_html = new_html.replace(cloze_old, cloze_new)
    print("Fixed cloze blank rendering logic")
else:
    print("Cloze blank logic check: already updated or pattern diff")

# 2. 修复 renderScopeBar (添加 data-scope 防止 active 样式丢失)
scope_bar_old = """    function renderScopeBar() {
      const container = document.getElementById('scopeBar');
      if (!container) return;
      const yearCards = ALL_CARDS.filter(c => c.year === state.activeYear);
      const texts = ['Text 1', 'Text 2', 'Text 3', 'Text 4'];
      
      let html = `<div class="scope-btn ${state.activeScope === 'all' ? 'active' : ''}" onclick="setScope('all')">🌟 ${state.activeYear} 全年通刷 (${yearCards.length}词)</div>`;
      
      texts.forEach(t => {
        const tCards = yearCards.filter(c => c.text === t);
        const count = tCards.length;
        const isAct = state.activeScope === t ? 'active' : '';
        if (count > 0) {
          html += `<div class="scope-btn ${isAct}" onclick="setScope('${t}')">${t} (${count}词)</div>`;
        } else {
          html += `<div class="scope-btn ${isAct}" style="opacity: 0.55;" onclick="alert('提示：${state.activeYear} 年 ${t} 的手写笔记图片尚未录入，待拍摄上传后会自动解锁！')">${t} (待补充照片)</div>`;
        }
      });
      container.innerHTML = html;
    }"""

scope_bar_new = """    function renderScopeBar() {
      const container = document.getElementById('scopeBar');
      if (!container) return;
      const yearCards = ALL_CARDS.filter(c => c.year === state.activeYear);
      const texts = ['Text 1', 'Text 2', 'Text 3', 'Text 4'];
      
      let html = `<div class="scope-btn ${state.activeScope === 'all' ? 'active' : ''}" data-scope="all" onclick="setScope('all')">🌟 ${state.activeYear} 全年通刷 (${yearCards.length}词)</div>`;
      
      texts.forEach(t => {
        const tCards = yearCards.filter(c => c.text === t);
        const count = tCards.length;
        const isAct = state.activeScope === t ? 'active' : '';
        if (count > 0) {
          html += `<div class="scope-btn ${isAct}" data-scope="${t}" onclick="setScope('${t}')">${t} (${count}词)</div>`;
        } else {
          html += `<div class="scope-btn ${isAct}" data-scope="${t}" style="opacity: 0.55;" onclick="alert('提示：${state.activeYear} 年 ${t} 的手写笔记图片尚未录入，待拍摄上传后会自动解锁！')">${t} (待补充照片)</div>`;
        }
      });
      container.innerHTML = html;
    }"""

if scope_bar_old in new_html:
    new_html = new_html.replace(scope_bar_old, scope_bar_new)
    print("Fixed renderScopeBar with data-scope attributes")
else:
    print("renderScopeBar check: already updated or pattern diff")

# 3. 修复 renderCategoryChips (添加 data-filter 确保分类筛选高亮及错题切换)
chips_old = """    function renderCategoryChips() {
      const container = document.getElementById('tagList');
      if (!container) return;
      const scoped = getScopedCards();
      const catNames = ['熟词生义', '固定短语', '核心词汇', '句型语法'];
      
      let html = `<div class="tag-chip ${state.activeFilter === 'all' ? 'active' : ''}" onclick="setFilter('all')">全部考点 (${scoped.length})</div>`;
      catNames.forEach(cat => {
        const cCount = scoped.filter(c => c.category === cat).length;
        html += `<div class="tag-chip ${state.activeFilter === cat ? 'active' : ''}" onclick="setFilter('${cat}')">${cat} (${cCount})</div>`;
      });
      const reviewCount = scoped.filter(c => state.reviewIds.has(c.id)).length;
      html += `<div class="tag-chip ${state.activeFilter === 'review' ? 'active' : ''}" onclick="setFilter('review')">只刷错题 (${reviewCount})</div>`;
      container.innerHTML = html;
    }"""

chips_new = """    function renderCategoryChips() {
      const container = document.getElementById('tagList');
      if (!container) return;
      const scoped = getScopedCards();
      const catNames = ['熟词生义', '固定短语', '核心词汇', '句型语法'];
      
      let html = `<div class="tag-chip ${state.activeFilter === 'all' ? 'active' : ''}" data-filter="all" onclick="setFilter('all')">全部考点 (${scoped.length})</div>`;
      catNames.forEach(cat => {
        const cCount = scoped.filter(c => c.category === cat).length;
        html += `<div class="tag-chip ${state.activeFilter === cat ? 'active' : ''}" data-filter="${cat}" onclick="setFilter('${cat}')">${cat} (${cCount})</div>`;
      });
      const reviewCount = scoped.filter(c => state.reviewIds.has(c.id)).length;
      html += `<div class="tag-chip ${state.activeFilter === 'review' ? 'active' : ''}" data-filter="review" onclick="setFilter('review')">只刷错题 (${reviewCount})</div>`;
      container.innerHTML = html;
    }"""

if chips_old in new_html:
    new_html = new_html.replace(chips_old, chips_new)
    print("Fixed renderCategoryChips with data-filter attributes")
else:
    print("renderCategoryChips check: already updated or pattern diff")

with open('考研英语刷题卡.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

with open('cards.json', 'w', encoding='utf-8') as f:
    json.dump(all_cards, f, ensure_ascii=False, indent=2)

print("Updated 考研英语刷题卡.html, index.html, and cards.json successfully!")

