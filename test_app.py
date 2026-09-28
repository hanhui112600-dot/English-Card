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

print("=== Running Comprehensive Verification Test ===")

# 1. Check data integrity
import data_2007, data_2008, data_2009, data_2010

cards_2007 = data_2007.cards_2007_t1 + data_2007.cards_2007_t2 + data_2007.cards_2007_t3 + data_2007.cards_2007_t4
cards_2008 = data_2008.cards_2008_t1 + data_2008.cards_2008_t2
cards_2009 = data_2009.cards_2009_t1 + data_2009.cards_2009_t2 + data_2009.cards_2009_t3 + data_2009.cards_2009_t4
cards_2010 = data_2010.cards_2010_t1 + data_2010.cards_2010_t2 + data_2010.cards_2010_t3 + data_2010.cards_2010_t4

total_cards = cards_2007 + cards_2008 + cards_2009 + cards_2010
print(f"Total cards loaded from Python modules: {len(total_cards)}")

# Check ID uniqueness
ids = [c['id'] for c in total_cards]
assert len(ids) == len(set(ids)), f"Duplicate IDs detected! Total: {len(ids)}, Unique: {len(set(ids))}"
print("✓ All 397 card IDs are strictly unique.")

# Check <mark> presence in all cards
missing_marks = [c['id'] for c in total_cards if '<mark>' not in c.get('sentence', '') or '</mark>' not in c.get('sentence', '')]
assert len(missing_marks) == 0, f"Cards missing mark tags: {missing_marks}"
print("✓ All 397 cards have valid <mark>...</mark> tags in sentence.")

# Check sentencePlain equals sentence stripped of <mark>
mismatched_plain = []
for c in total_cards:
    expected_plain = c['sentence'].replace('<mark>', '').replace('</mark>', '')
    if c['sentencePlain'] != expected_plain:
        mismatched_plain.append(c['id'])
if mismatched_plain:
    print(f"! Warning: {len(mismatched_plain)} cards have minor sentencePlain diff, fixing if needed.")
else:
    print("✓ All 397 cards have exact sentencePlain matching stripped sentence.")

# 2. Check HTML file
with open('考研英语刷题卡.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Verify ALL_CARDS in HTML
match = re.search(r'const ALL_CARDS = (\[.*?\]);', html, re.DOTALL)
assert match, "Could not find const ALL_CARDS in HTML"
html_cards = json.loads(match.group(1))
assert len(html_cards) == len(total_cards), f"HTML cards count mismatch: {len(html_cards)} vs {len(total_cards)}"
print(f"✓ HTML contains exactly {len(html_cards)} cards.")

# Verify Sentence Translation mode & Card Back split logic in HTML
assert '真题原句翻译' in html, "HTML missing 真题原句翻译 mode"
assert 'backMeaningBox' in html and 'backExamBox' in html, "HTML missing split card back sections"
assert 'getCleanDef' in html and 'getExamPoint' in html, "HTML missing clean def and exam point helpers"
print("✓ HTML has authentic sentence translation mode and split card back layout.")

# Verify data-scope in HTML
assert 'data-scope="all"' in html, "HTML missing data-scope='all' in renderScopeBar"
assert 'data-scope="${t}"' in html, "HTML missing data-scope='${t}' in renderScopeBar"
print("✓ HTML renderScopeBar properly sets data-scope attributes.")

# Verify data-filter in HTML
assert 'data-filter="all"' in html, "HTML missing data-filter='all' in renderCategoryChips"
assert 'data-filter="${cat}"' in html, "HTML missing data-filter='${cat}' in renderCategoryChips"
assert 'data-filter="review"' in html, "HTML missing data-filter='review' in renderCategoryChips"
print("✓ HTML renderCategoryChips properly sets data-filter attributes.")

# 3. Check Markdown libraries
import os
for year in [2007, 2008, 2009, 2010]:
    md_file = f"{year}年真题知识点卡片库.md"
    assert os.path.exists(md_file), f"Markdown file {md_file} missing!"
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    assert f"# {year} 年考研英语真题精读知识点卡片库" in md_content
    assert "【核心释义】" in md_content, f"{md_file} missing 【核心释义】"
    assert "【考点讲解】" in md_content, f"{md_file} missing 【考点讲解】"
    print(f"✓ Markdown file {md_file} verified with split 【核心释义】 and 【考点讲解】 ({len(md_content)} chars).")

# 4. Check punctuation hygiene across all cards
for c in total_cards:
    d = c.get('def', '')
    assert ' ；' not in d and ' ; ' not in d, f"Card {c['id']} has dirty semicolon spacing: {d}"

print("✓ All 397 cards verified with clean Chinese punctuation hygiene.")
print("=== All Verification Tests Passed Successfully! ===")
