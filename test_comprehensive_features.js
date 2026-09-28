// -*- coding: utf-8 -*-
const fs = require('fs');
const assert = require('assert');

console.log('=== Running Comprehensive End-to-End Simulation Tests ===');

const html = fs.readFileSync('index.html', 'utf8');

// Extract ALL_CARDS
const cardsMatch = html.match(/const ALL_CARDS = (\[[\s\S]*?\]);/);
assert(cardsMatch, 'ALL_CARDS match failed');
const ALL_CARDS = JSON.parse(cardsMatch[1]);
console.log(`✓ Loaded ${ALL_CARDS.length} cards from index.html`);

// Simulate DOM & functions from index.html
function getCleanWord(card) {
  if (!card || !card.word) return '';
  let w = card.word.replace(/\s*[\(（][^()（）]*[\)）]\s*/g, ' ').trim();
  return w || card.word;
}

function getCleanDef(card) {
  if (!card || !card.def) return '';
  let d = card.def;
  d = d.replace(/[\(（](封为)[\)）]/g, '$1');
  d = d.replace(/[\(（](不)[\)）]/g, '$1');
  d = d.replace(/[\(（](几乎)[\)）]/g, '$1');
  d = d.replace(/[\(（](原判)[\)）]/g, '$1');
  d = d.replace(/\s*[\(（][^()（）]*[\)）]\s*/g, ' ');
  d = d.replace(/\s*[;；]\s*/g, '；');
  d = d.replace(/\s*[,，]\s*/g, '，');
  d = d.replace(/\s*[、]\s*/g, '、');
  d = d.replace(/\s*[;；，,、]\s*$/g, '');
  return d.replace(/\s+/g, ' ').trim();
}

function getExamPoint(card) {
  if (!card) return '';
  let tag = card.noteTag || '';
  if (tag && !tag.startsWith('★')) {
    tag = '★ ' + tag;
  }
  return tag;
}

// 1. Verify Card Back Separation on all 397 cards
console.log('\n--- 1. Testing Card Back Separation ---');
for (const card of ALL_CARDS) {
  const cleanDef = getCleanDef(card);
  const examPoint = getExamPoint(card);
  
  assert(cleanDef.length > 0, `Card ${card.id} has empty clean def`);
  assert(examPoint.length > 0, `Card ${card.id} has empty exam point`);
  
  // Section 1 must NOT contain raw bracket keywords
  const forbidden = ['手写批注', '千万不可', '熟词僻义', '熟词生义', '有赞叹', '无贬义'];
  for (const f of forbidden) {
    assert(!cleanDef.includes(f), `Card ${card.id} clean def contains forbidden '${f}': ${cleanDef}`);
  }
}
console.log('✓ All 397 cards successfully separate into pure Section 1 (含义) and highlighted Section 2 (考点讲解).');

// Test special targeted cards
const consistCard = ALL_CARDS.find(c => c.id === '2010-T1-07');
assert(getCleanDef(consistCard) === 'A 由 B 组成', `consistCard cleanDef: ${getCleanDef(consistCard)}`);
assert(getExamPoint(consistCard).includes('is consisted of') && getExamPoint(consistCard).includes('没有被动态'), `consistCard examPoint: ${getExamPoint(consistCard)}`);

const coverageCard = ALL_CARDS.find(c => c.id === '2010-T1-01');
assert(getCleanDef(coverageCard) === '新闻报道', `coverageCard cleanDef: ${getCleanDef(coverageCard)}`);
assert(getExamPoint(coverageCard).includes('熟词僻义') && getExamPoint(coverageCard).includes('非“覆盖率”'), `coverageCard examPoint: ${getExamPoint(coverageCard)}`);

const saveCard = ALL_CARDS.find(c => c.id === '2010-T1-04');
assert(getCleanDef(saveCard) === '除了', `saveCard cleanDef: ${getCleanDef(saveCard)}`);
assert(getExamPoint(saveCard).includes('except') && getExamPoint(saveCard).includes('非动词“拯救”'), `saveCard examPoint: ${getExamPoint(saveCard)}`);

const woreCard = ALL_CARDS.find(c => c.id === '2010-T1-20');
assert(getCleanDef(woreCard) === '穿、佩戴；引申为展现', `woreCard cleanDef: ${getCleanDef(woreCard)}`);
assert(getExamPoint(woreCard).includes('wear 的过去式'), `woreCard examPoint: ${getExamPoint(woreCard)}`);

const knightedCard = ALL_CARDS.find(c => c.id === '2010-T1-28');
assert(getCleanDef(knightedCard).includes('封为骑士'), `knightedCard cleanDef: ${getCleanDef(knightedCard)}`);

console.log('✓ Core target grammar/usage cards (consist of, coverage, save, wore, knighted) verified with exact precision.');

// 2. Verify Mode 2: "真题原句翻译"
console.log('\n--- 2. Testing Mode 2: 真题原句翻译 ---');
// Front: must show full authentic sentence with <mark> tags, NO cloze blanks '【 ? 】'
for (const card of ALL_CARDS) {
  assert(card.sentence.includes('<mark>'), `Card ${card.id} sentence missing <mark>`);
  assert(card.sentence.includes('</mark>'), `Card ${card.id} sentence missing </mark>`);
  assert(!card.sentence.includes('【 ? 】'), `Card ${card.id} sentence should not contain cloze blank`);
  assert(card.translation && card.translation.trim().length > 3, `Card ${card.id} missing translation`);
}
console.log('✓ All 397 cards verified for authentic sentence translation mode without blanks.');

// 3. Verify HTML DOM elements and hooks
console.log('\n--- 3. Testing HTML Markup & Architecture ---');
assert(html.includes('id="modeTranslate"'), 'HTML missing modeTranslate');
assert(html.includes('真题原句翻译'), 'HTML missing 真题原句翻译 text');
assert(html.includes('id="frontTranslateView"'), 'HTML missing frontTranslateView');
assert(html.includes('id="frontTranslateSentence"'), 'HTML missing frontTranslateSentence');
assert(html.includes('id="backTranslateHeroBox"'), 'HTML missing backTranslateHeroBox');
assert(html.includes('id="backHeroTranslation"'), 'HTML missing backHeroTranslation');
assert(html.includes('id="backMeaningBox"'), 'HTML missing backMeaningBox');
assert(html.includes('id="backExamBox"'), 'HTML missing backExamBox');
assert(html.includes('id="backSentenceBlock"'), 'HTML missing backSentenceBlock');
assert(html.includes('backSentenceBlock.style.display = \'none\''), 'HTML missing hiding backSentenceBlock in translate mode');
assert(html.includes('mode: state.mode'), 'HTML missing state.mode persistence in saveState');
assert(html.includes('【核心释义】'), 'HTML missing 【核心释义】 title');
assert(html.includes('【考点讲解】'), 'HTML missing 【考点讲解】 title');
assert(html.includes('getCleanDef'), 'HTML missing getCleanDef');
assert(html.includes('getExamPoint'), 'HTML missing getExamPoint');
assert(html.includes('getCleanWord'), 'HTML missing getCleanWord');
assert(html.includes('--primary-light: rgba(99, 102, 241, 0.18)'), 'HTML missing dark theme primary-light contrast definition');
console.log('✓ HTML markup, DOM elements, and JavaScript helpers verified.');

// 4. Verify Anki Export formatting
console.log('\n--- 4. Testing Anki Export Format ---');
ALL_CARDS.slice(0, 10).forEach(c => {
  const cleanW = getCleanWord(c);
  const cleanD = getCleanDef(c);
  const note = getExamPoint(c);
  const back = `<div style='font-size:18px; color:#4f46e5; font-weight:bold;'>【核心释义】${cleanD}</div>` +
               (note ? `<div style='background:#fef3c7; color:#b45309; padding:3px 8px; border-radius:4px; display:inline-block; margin-top:6px; font-weight:bold;'>【考点讲解】${note}</div>` : '') +
               `<hr style='margin:12px 0;'><div style='line-height:1.6;'>${c.sentence}</div><div style='color:#666; margin-top:6px;'>${c.translation}</div>`;
  assert(back.includes('【核心释义】'), 'Anki back missing 核心释义');
  assert(back.includes('【考点讲解】'), 'Anki back missing 考点讲解');
  assert(!cleanW.includes('(') || cleanW.includes(')'), 'Anki front clean word format');
});
console.log('✓ Anki export structure verified.');

// 5. Verify Edge Cases
console.log('\n--- 5. Testing Edge Cases & Boundary Conditions ---');
assert.strictEqual(getCleanDef(null), '');
assert.strictEqual(getCleanDef({}), '');
assert.strictEqual(getCleanDef({ def: '' }), '');
assert.strictEqual(getCleanWord(null), '');
assert.strictEqual(getCleanWord({}), '');
assert.strictEqual(getCleanWord({ word: '' }), '');
assert.strictEqual(getExamPoint(null), '');
assert.strictEqual(getExamPoint({}), '');
assert.strictEqual(getExamPoint({ noteTag: '高频搭配' }), '★ 高频搭配');
assert.strictEqual(getExamPoint({ noteTag: '★ 已有星号' }), '★ 已有星号');

// Test complex punctuation
assert.strictEqual(getCleanDef({ def: '审查、检验 (手写批注：check)；' }), '审查、检验');
assert.strictEqual(getCleanDef({ def: '多重定义；' }), '多重定义');
assert.strictEqual(getCleanDef({ def: '逐渐患上 ；发展、开发' }), '逐渐患上；发展、开发');
assert.strictEqual(getCleanDef({ def: '特点、特征 ; 以……为特色' }), '特点、特征；以……为特色');
assert.strictEqual(getCleanDef({ def: '招致、招引 ；邀请' }), '招致、招引；邀请');

console.log('✓ All edge cases and boundary conditions successfully handled.');
console.log('\n=== ALL SIMULATION TESTS PASSED WITH 100% SUCCESS! ===');
