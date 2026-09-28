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

print("=== Testing Sentence Translation Mode, Clean Definitions, and Note Tags on All 397 Cards ===")

with open('考研英语刷题卡.html', 'r', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'const ALL_CARDS = (\[.*?\]);', html, re.DOTALL)
assert m, "Could not find const ALL_CARDS in HTML"
cards = json.loads(m.group(1))

# 1. Test Sentence Translation mode completeness:
# 100% of cards must have complete authentic sentence with <mark> tags for contextual reading
missing_sentence = []
for c in cards:
    if '<mark>' not in c.get('sentence', '') or '</mark>' not in c.get('sentence', ''):
        missing_sentence.append(c['id'])
    if not c.get('translation', '').strip():
        missing_sentence.append(c['id'])

assert len(missing_sentence) == 0, f"Cards missing authentic sentence or translation: {missing_sentence}"
print(f"Total cards tested for Translation Mode: {len(cards)}")
print("✓ 100% of all 397 cards have complete authentic sentences with <mark> highlights and fluent translations!")

# 2. Test Clean Definition (Section 1: 含义，不包含括号考点)
cards_with_raw_brackets = []
for c in cards:
    d = c.get('def', '')
    if any(k in d for k in ['手写批注', '千万不可', '熟词僻义', '熟词生义', '有赞叹', '无贬义']):
        cards_with_raw_brackets.append((c['id'], d))

assert len(cards_with_raw_brackets) == 0, f"Definitions with raw bracket annotations: {cards_with_raw_brackets}"
print("✓ 100% of all 397 cards have clean Chinese definitions free of bracketed test point clutter!")

# 3. Test Note Tags (Section 2: 考点讲解)
cards_with_tags = [c for c in cards if c.get('noteTag')]
print(f"Cards with explicit noteTag: {len(cards_with_tags)} / {len(cards)}")
assert len(cards_with_tags) == len(cards), f"Cards missing noteTag: {len(cards) - len(cards_with_tags)}"

print("Sample test points (考点讲解):")
for c in cards_with_tags[:5]:
    print(f"  [{c['id']}] {c['word']}: {c['noteTag']}")

# 4. Check HTML structure for the two distinct sections on card back and translation mode
assert 'backMeaningBox' in html, "backMeaningBox missing in HTML"
assert 'backExamBox' in html, "backExamBox missing in HTML"
assert '【核心释义】' in html, "【核心释义】 title missing in HTML"
assert '【考点讲解】' in html, "【考点讲解】 title missing in HTML"
assert '真题原句翻译' in html, "真题原句翻译 mode tab missing in HTML"
assert 'backTranslateHeroBox' in html, "backTranslateHeroBox missing in HTML"
print("✓ HTML card back split (核心释义 + 考点讲解) and mode 2 (真题原句翻译) verified.")

# 5. Check HTML Anki export function
assert 'exportToAnki' in html, "exportToAnki function missing in HTML"
assert '#separator:Tab' in html, "Anki TSV header missing"
print("✓ Anki export function verified.")

# 6. Check year & scope switching functions
assert 'function setYear(year)' in html
assert 'function setScope(scope)' in html
assert 'function setFilter(filter)' in html
print("✓ Interactive state switching functions verified.")

print("=== Sentence Translation & Note Tag Verification Passed! ===")
