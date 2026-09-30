// -*- coding: utf-8 -*-
/**
 * test_plan_and_quota.js
 * Comprehensive Verification Suite for Multi-Plan Scheme Selector, Custom Plan Start Date,
 * Daily Quota Progress & Cross-Day Scheduling, Breakpoint Resume & Year Advancement.
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

console.log('=== Running Plan, Quota, Breakpoint & Advancement Verification Suite ===\n');

// 1. Verify HTML Files & DOM Elements
const htmlFiles = ['index.html', '考研英语刷题卡.html'];
for (const file of htmlFiles) {
  const content = fs.readFileSync(path.join(__dirname, file), 'utf8');

  // Verify Header Progress Pill
  assert(content.includes('id="headerPlanPill"'), `${file} missing headerPlanPill element`);
  assert(content.includes('.plan-header-pill'), `${file} missing .plan-header-pill CSS`);
  assert(content.includes('openPlanModal()'), `${file} missing openPlanModal trigger`);

  // Verify Drawer Plan Section
  assert(content.includes('id="drawerPlanName"'), `${file} missing drawerPlanName element`);
  assert(content.includes('id="drawerPlanDesc"'), `${file} missing drawerPlanDesc element`);

  // Verify Daily Goal Celebration Modal & Buttons
  assert(content.includes('id="dailyGoalModal"'), `${file} missing dailyGoalModal element`);
  assert(content.includes('id="btnGoalDone"'), `${file} missing btnGoalDone element`);
  assert(content.includes('id="btnGoalContinue"'), `${file} missing btnGoalContinue element`);
  assert(content.includes('今日圆满打卡 ☕'), `${file} missing '今日圆满打卡 ☕' button text`);
  assert(content.includes('学有余力，继续挑战 ➔'), `${file} missing '学有余力，继续挑战 ➔' button text`);

  // Verify Multi-Plan Selector Modal & Custom Start Date / Target / Deadline Inputs
  assert(content.includes('id="planModal"'), `${file} missing planModal element`);
  assert(content.includes('id="planStartDateInput"'), `${file} missing planStartDateInput element`);
  assert(content.includes('onPlanStartDateChange'), `${file} missing onPlanStartDateChange handler`);
  assert(content.includes('id="planOptionsList"'), `${file} missing planOptionsList container`);
  assert(content.includes('id="customPlanInputBox"'), `${file} missing customPlanInputBox container`);
  assert(content.includes('id="customTargetInput"'), `${file} missing customTargetInput element`);
  assert(content.includes('id="customDeadlineInput"'), `${file} missing customDeadlineInput element`);
  assert(content.includes('onCustomDeadlineChange'), `${file} missing onCustomDeadlineChange handler`);
  assert(content.includes('id="planModalFooterStats"'), `${file} missing planModalFooterStats container`);
  assert(content.includes('id="planModalFooterETD"'), `${file} missing planModalFooterETD element`);
  assert(content.includes('saveSelectedPlan'), `${file} missing saveSelectedPlan trigger`);

  // Verify Version Alignment
  assert(content.includes("const APP_VERSION = '1.2.1';"), `${file} APP_VERSION != 1.2.1`);
  assert(content.includes("题库版本：v1.2.1"), `${file} version display != v1.2.1`);

  console.log(`✓ 1. DOM Architecture & UI Elements verified in ${file}`);
}

// 2. Unit Testing Multi-Plan Scheme Selector, Custom Start Date & ETD Calculation Logic
console.log('\n--- 2. Testing Multi-Plan Scheme Selector, Start Date & ETD Calculation ---');

const PLAN_PRESETS = {
  steady: { id: 'steady', name: '稳步精读型', icon: '🌿', dailyTarget: 35 },
  intensive: { id: 'intensive', name: '高效强化型', icon: '⚡', dailyTarget: 60 },
  yearly: { id: 'yearly', name: '整年通刷型', icon: '🔥', dailyTarget: null },
  custom: { id: 'custom', name: '自定义目标型', icon: '⚙️', dailyTarget: 50 }
};

function isFuturePlanStartDate(state, todayStr = '2026-09-29') {
  if (!state.plan || !state.plan.startDate) return false;
  const today = new Date(todayStr + 'T00:00:00');
  const start = new Date(state.plan.startDate + 'T00:00:00');
  return start.getTime() > today.getTime();
}

function getDaysUntilPlanStart(state, todayStr = '2026-09-29') {
  if (!state.plan || !state.plan.startDate) return 0;
  const today = new Date(todayStr + 'T00:00:00');
  const start = new Date(state.plan.startDate + 'T00:00:00');
  return Math.ceil((start.getTime() - today.getTime()) / 86400000);
}

function getDailyTarget(state, allCards, todayStr = '2026-09-29') {
  const m = (state.plan && state.plan.mode) || 'intensive';
  if (m === 'steady') return 35;
  if (m === 'intensive') return 60;
  if (m === 'yearly') {
    const yearCards = allCards.filter(c => c.year === state.activeYear);
    return Math.max(yearCards.length, 1);
  }
  if (m === 'custom') {
    if (state.plan && state.plan.customDeadline) {
      const today = new Date(todayStr + 'T00:00:00');
      const startStr = (state.plan && state.plan.startDate) ? state.plan.startDate : todayStr;
      const startDate = new Date(startStr + 'T00:00:00');
      const baseDate = startDate > today ? startDate : today;
      const targetDate = new Date(state.plan.customDeadline + 'T00:00:00');
      const diffDays = Math.ceil((targetDate.getTime() - baseDate.getTime()) / (1000 * 3600 * 24));
      if (diffDays > 0) {
        const unmastered = allCards.filter(c => !state.masteredIds.has(c.id)).length;
        return Math.max(Math.ceil(unmastered / diffDays), 1);
      }
    }
    return Math.max(parseInt(state.plan.customDailyTarget, 10) || 50, 1);
  }
  return 60;
}

function getETDInfo(state, allCards, todayStr = '2026-09-29') {
  const unmastered = allCards.filter(c => !state.masteredIds.has(c.id)).length;
  if (unmastered === 0) {
    return { unmastered: 0, daysRemaining: 0, etdStr: '已全量通关 🎉' };
  }
  const today = new Date(todayStr + 'T00:00:00');
  const startStr = (state.plan && state.plan.startDate) ? state.plan.startDate : todayStr;
  const startDate = new Date(startStr + 'T00:00:00');
  const baseDate = startDate > today ? startDate : today;

  if (state.plan && state.plan.mode === 'custom' && state.plan.customDeadline) {
    const targetDate = new Date(state.plan.customDeadline + 'T00:00:00');
    const diffDays = Math.ceil((targetDate.getTime() - baseDate.getTime()) / (1000 * 3600 * 24));
    if (diffDays > 0) {
      const finishDate = targetDate;
      const etdStr = `${finishDate.getMonth() + 1}月${finishDate.getDate()}日`;
      const daysRemaining = Math.ceil((finishDate.getTime() - today.getTime()) / (1000 * 3600 * 24));
      return { unmastered, daysRemaining, etdStr };
    }
  }
  const dailyTarget = getDailyTarget(state, allCards, todayStr);
  const studyDays = Math.ceil(unmastered / Math.max(dailyTarget, 1));
  const finishDate = new Date(baseDate.getTime() + studyDays * 86400000);
  const etdStr = `${finishDate.getMonth() + 1}月${finishDate.getDate()}日`;
  const daysRemaining = Math.ceil((finishDate.getTime() - today.getTime()) / 86400000);
  return { unmastered, daysRemaining, etdStr };
}

// Mock cards (397 cards across 2007-2010)
const mockCards = [];
for (let yr = 2007; yr <= 2010; yr++) {
  const count = (yr === 2008 ? 71 : (yr === 2007 ? 112 : (yr === 2009 ? 112 : 102)));
  for (let i = 1; i <= count; i++) {
    mockCards.push({ id: `${yr}-T1-${String(i).padStart(2, '0')}`, year: yr, text: 'Text 1' });
  }
}
assert.strictEqual(mockCards.length, 397, "Mock cards total should match 397");

// Test default Intensive plan (60 words/day, no startDate set)
let simState = {
  activeYear: 2010,
  masteredIds: new Set(),
  plan: { mode: 'intensive', customDailyTarget: 50, customDeadline: '', startDate: '' }
};
assert.strictEqual(getDailyTarget(simState, mockCards), 60);
let etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.unmastered, 397);
assert.strictEqual(etd.daysRemaining, Math.ceil(397 / 60)); // 7 days
assert(etd.etdStr.includes('月'), "ETD should format with M月D日");

// Test Steady plan (35 words/day)
simState.plan.mode = 'steady';
assert.strictEqual(getDailyTarget(simState, mockCards), 35);
etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.daysRemaining, Math.ceil(397 / 35)); // 12 days

// Test Yearly plan
simState.plan.mode = 'yearly';
simState.activeYear = 2008; // 71 cards
assert.strictEqual(getDailyTarget(simState, mockCards), 71);
simState.activeYear = 2010; // 102 cards
assert.strictEqual(getDailyTarget(simState, mockCards), 102);

// Test Custom plan with daily target (50 words/day, 100 words/day)
simState.plan.mode = 'custom';
simState.plan.customDailyTarget = 50;
simState.plan.customDeadline = '';
assert.strictEqual(getDailyTarget(simState, mockCards), 50);
etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.daysRemaining, Math.ceil(397 / 50)); // 8 days

simState.plan.customDailyTarget = 100;
assert.strictEqual(getDailyTarget(simState, mockCards), 100);
etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.daysRemaining, Math.ceil(397 / 100)); // 4 days

// Test Custom plan with target deadline (e.g. 10 days away: 2026-10-09)
simState.plan.customDeadline = '2026-10-09';
const expectedTarget = Math.ceil(397 / 10); // 40 words/day
assert.strictEqual(getDailyTarget(simState, mockCards, '2026-09-29'), expectedTarget);
etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.daysRemaining, 10);
assert.strictEqual(etd.etdStr, '10月9日');

// Test Custom plan with past/today deadline: gracefully falls back to customDailyTarget
simState.plan.customDeadline = '2026-09-28'; // in the past
assert.strictEqual(getDailyTarget(simState, mockCards, '2026-09-29'), 100, "Must fall back to customDailyTarget");

// --- 2b. Testing Custom Plan Start Date: Future, Today, and Past dates ---
console.log('\n--- 2b. Testing Custom Plan Start Date Dynamics (Future, Today, Past) ---');

// Case A: Future Start Date (today: 2026-09-29, startDate: 2026-10-01, 2 days away)
simState.plan.mode = 'intensive'; // 60 cards/day -> 7 study days
simState.plan.startDate = '2026-10-01';
simState.plan.customDeadline = '';
assert.strictEqual(isFuturePlanStartDate(simState, '2026-09-29'), true, "Must detect future start date");
assert.strictEqual(getDaysUntilPlanStart(simState, '2026-09-29'), 2, "2 days until 2026-10-01");
etd = getETDInfo(simState, mockCards, '2026-09-29');
// Study period starts from 2026-10-01, 7 days later = 2026-10-08
assert.strictEqual(etd.etdStr, '10月8日', "ETD must calculate from future start date");
// Total days remaining from today (2026-09-29) to 2026-10-08 is 9 days
assert.strictEqual(etd.daysRemaining, 9, "Days remaining from today must include lead time");

// Case B: Future Start Date with Custom Deadline (startDate: 2026-10-01, deadline: 2026-10-11)
simState.plan.mode = 'custom';
simState.plan.customDeadline = '2026-10-11';
// Available study days from start date = 10 days
const futureTarget = getDailyTarget(simState, mockCards, '2026-09-29');
assert.strictEqual(futureTarget, Math.ceil(397 / 10), "Target must be computed from start date to deadline");
assert.strictEqual(futureTarget, 40);
etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.etdStr, '10月11日');
assert.strictEqual(etd.daysRemaining, 12); // 2 lead days + 10 study days

// Case C: Today Start Date (today: 2026-09-29, startDate: 2026-09-29)
simState.plan.mode = 'intensive';
simState.plan.startDate = '2026-09-29';
simState.plan.customDeadline = '';
assert.strictEqual(isFuturePlanStartDate(simState, '2026-09-29'), false, "Today start date is not future");
etd = getETDInfo(simState, mockCards, '2026-09-29');
assert.strictEqual(etd.daysRemaining, 7, "Today start date gives standard 7 days");
assert.strictEqual(etd.etdStr, '10月6日');

// Case D: Past Start Date (today: 2026-09-29, startDate: 2026-09-20, 9 days ago)
simState.plan.startDate = '2026-09-20';
assert.strictEqual(isFuturePlanStartDate(simState, '2026-09-29'), false, "Past start date is not future");
etd = getETDInfo(simState, mockCards, '2026-09-29');
// Remaining unmastered cards need 7 days starting today
assert.strictEqual(etd.daysRemaining, 7);
assert.strictEqual(etd.etdStr, '10月6日');

// Test 100% mastered completion ETD
mockCards.forEach(c => simState.masteredIds.add(c.id));
etd = getETDInfo(simState, mockCards);
assert.strictEqual(etd.unmastered, 0);
assert.strictEqual(etd.daysRemaining, 0);
assert.strictEqual(etd.etdStr, '已全量通关 🎉');

console.log('✓ 2. All 4 plan modes, target adjustments, custom start dates (future/today/past), deadline calculation, and dynamic ETD calculations verified.');


// 3. Testing Daily Quota, Celebration Trigger & Calendar Day Transitions
console.log('\n--- 3. Testing Daily Quota, Celebration & Cross-Day Scheduling ---');

function formatHeaderPlanPill(state, allCards, todayStr = '2026-09-29') {
  if (isFuturePlanStartDate(state, todayStr)) {
    const startObj = new Date(state.plan.startDate + 'T00:00:00');
    const diffDays = getDaysUntilPlanStart(state, todayStr);
    return `🎯 计划将于 ${startObj.getMonth() + 1}月${startObj.getDate()}日 正式启动 (还剩 ${diffDays} 天) · 当前可自由预习`;
  }
  const todayCount = state.daily && state.daily.todayLearnedIds ? state.daily.todayLearnedIds.length : 0;
  const target = getDailyTarget(state, allCards, todayStr);
  const streak = state.daily ? state.daily.streakDays : 1;
  const { unmastered, etdStr } = getETDInfo(state, allCards, todayStr);

  const etdPart = unmastered === 0 ? '预计 已全量通关 🎉' : `预计 ${etdStr} 全量通关`;
  return `🎯 今日计划: ${todayCount} / ${target} 词 | 🔥 连续打卡 ${streak} 天 | ${etdPart}`;
}

function simulateDayTransition(state, newDateStr) {
  if (!state.daily || !state.daily.date) {
    state.daily = {
      date: newDateStr,
      todayLearnedIds: [],
      streakDays: 1,
      lastStudyDate: newDateStr,
      lastCheckinDate: null,
      goalCelebrated: false
    };
    return;
  }

  const prevDate = new Date(state.daily.date + 'T00:00:00');
  const currDate = new Date(newDateStr + 'T00:00:00');
  const diffDays = Math.round((currDate.getTime() - prevDate.getTime()) / (1000 * 3600 * 24));

  // Reset today learned count & goal celebration
  state.daily.todayLearnedIds = [];
  state.daily.goalCelebrated = false;
  state.daily.date = newDateStr;

  const yesterday = new Date(currDate);
  yesterday.setDate(yesterday.getDate() - 1);
  const yesterdayStr = `${yesterday.getFullYear()}-${String(yesterday.getMonth()+1).padStart(2,'0')}-${String(yesterday.getDate()).padStart(2,'0')}`;

  // Streak preservation rule:
  // If consecutive day AND user checked in yesterday, streakDays is preserved!
  // If user skipped multi-day without opening, or yesterday did not check-in, streak resets to 1.
  if (diffDays > 1 || (state.daily.lastCheckinDate && state.daily.lastCheckinDate !== yesterdayStr)) {
    state.daily.streakDays = 1;
  }
}

function simulateCardStudy(state, allCards, cardId, onCelebrationModal, todayStr = '2026-09-29') {
  if (!state.daily.todayLearnedIds.includes(cardId)) {
    state.daily.todayLearnedIds.push(cardId);
  }
  // Free preview mode before plan start date:
  if (isFuturePlanStartDate(state, todayStr)) {
    return;
  }
  const target = getDailyTarget(state, allCards, todayStr);
  if (state.daily.todayLearnedIds.length >= target && !state.daily.goalCelebrated) {
    state.daily.goalCelebrated = true;
    // Check-in logic:
    if (state.daily.lastCheckinDate !== state.daily.date) {
      const prevDate = new Date(state.daily.date + 'T00:00:00');
      prevDate.setDate(prevDate.getDate() - 1);
      const yesterdayStr = `${prevDate.getFullYear()}-${String(prevDate.getMonth()+1).padStart(2,'0')}-${String(prevDate.getDate()).padStart(2,'0')}`;

      if (state.daily.lastCheckinDate === yesterdayStr) {
        state.daily.streakDays = (state.daily.streakDays || 1) + 1;
      } else {
        state.daily.streakDays = 1;
      }
      state.daily.lastCheckinDate = state.daily.date;
    }
    if (onCelebrationModal) onCelebrationModal();
  }
}

// Scenario 1: Future Start Date Preview vs Date Arrival
console.log('\n--- Testing Future Start Date Pre-study and Arrival Date Activation ---');
let futureStudyState = {
  activeYear: 2010,
  masteredIds: new Set(),
  plan: { mode: 'intensive', customDailyTarget: 50, customDeadline: '', startDate: '2026-10-01' },
  daily: {
    date: '2026-09-30',
    todayLearnedIds: [],
    streakDays: 1,
    lastStudyDate: '2026-09-30',
    lastCheckinDate: null,
    goalCelebrated: false
  }
};
// 1. On 2026-09-30 (1 day before start date 2026-10-01):
let futurePill = formatHeaderPlanPill(futureStudyState, mockCards, '2026-09-30');
assert.strictEqual(futurePill, '🎯 计划将于 10月1日 正式启动 (还剩 1 天) · 当前可自由预习');

// User previews 65 cards on 2026-09-30:
let celebrationCalled = false;
for (let i = 0; i < 65; i++) {
  simulateCardStudy(futureStudyState, mockCards, mockCards[i].id, () => { celebrationCalled = true; }, '2026-09-30');
}
assert.strictEqual(futureStudyState.daily.todayLearnedIds.length, 65, "Preview cards recorded in learned set");
assert.strictEqual(celebrationCalled, false, "Must not trigger celebration modal before plan start date");
assert.strictEqual(futureStudyState.daily.goalCelebrated, false);

// 2. Day arrives (2026-10-01): Start date is today!
simulateDayTransition(futureStudyState, '2026-10-01');
assert.strictEqual(isFuturePlanStartDate(futureStudyState, '2026-10-01'), false, "Plan is now active!");
let arrivedPill = formatHeaderPlanPill(futureStudyState, mockCards, '2026-10-01');
assert(arrivedPill.startsWith('🎯 今日计划: 0 / 60 词 | 🔥 连续打卡 1 天'));

// Now study 60 cards on arrival date: Daily quota celebration kicks off!
celebrationCalled = false;
for (let i = 0; i < 60; i++) {
  simulateCardStudy(futureStudyState, mockCards, mockCards[i + 70].id, () => { celebrationCalled = true; }, '2026-10-01');
}
assert.strictEqual(celebrationCalled, true, "Celebration kicks off on arrival date!");
assert.strictEqual(futureStudyState.daily.goalCelebrated, true);
assert.strictEqual(futureStudyState.daily.lastCheckinDate, '2026-10-01');

// Scenario 2: Day 1 (2026-09-29) - Intensive Plan (60 words) standard execution
let studyState = {
  activeYear: 2010,
  masteredIds: new Set(),
  plan: { mode: 'intensive', customDailyTarget: 50, customDeadline: '', startDate: '2026-09-29' },
  daily: {
    date: '2026-09-29',
    todayLearnedIds: [],
    streakDays: 1,
    lastStudyDate: '2026-09-29',
    lastCheckinDate: null,
    goalCelebrated: false
  }
};

let pillText = formatHeaderPlanPill(studyState, mockCards, '2026-09-29');
assert(pillText.startsWith('🎯 今日计划: 0 / 60 词 | 🔥 连续打卡 1 天 | 预计'));

// Study 59 cards: quota not yet reached
let celebrationTriggered = false;
for (let i = 0; i < 59; i++) {
  simulateCardStudy(studyState, mockCards, mockCards[i].id, () => { celebrationTriggered = true; });
}
assert.strictEqual(studyState.daily.todayLearnedIds.length, 59);
assert.strictEqual(celebrationTriggered, false);
assert.strictEqual(studyState.daily.goalCelebrated, false);

// Study 60th card: triggers celebration!
simulateCardStudy(studyState, mockCards, mockCards[59].id, () => { celebrationTriggered = true; });
assert.strictEqual(studyState.daily.todayLearnedIds.length, 60);
assert.strictEqual(celebrationTriggered, true);
assert.strictEqual(studyState.daily.goalCelebrated, true);
assert.strictEqual(studyState.daily.lastCheckinDate, '2026-09-29');
assert.strictEqual(studyState.daily.streakDays, 1);

// Study 61st card: "学有余力，继续挑战", should accumulate beyond 60 without re-triggering celebration modal
celebrationTriggered = false;
simulateCardStudy(studyState, mockCards, mockCards[60].id, () => { celebrationTriggered = true; });
assert.strictEqual(studyState.daily.todayLearnedIds.length, 61);
assert.strictEqual(celebrationTriggered, false); // No redundant popup!

pillText = formatHeaderPlanPill(studyState, mockCards, '2026-09-29');
assert(pillText.includes('61 / 60 词'));

// Transition to Day 2 (2026-09-30): consecutive day
simulateDayTransition(studyState, '2026-09-30');
// Verify: learned count is reset to 0, but streakDays is STRICTLY PRESERVED!
assert.strictEqual(studyState.daily.todayLearnedIds.length, 0, "Learned count must reset to 0 on new date");
assert.strictEqual(studyState.daily.streakDays, 1, "streakDays must be preserved across consecutive days");
assert.strictEqual(studyState.daily.goalCelebrated, false, "goalCelebrated must reset for new date");

pillText = formatHeaderPlanPill(studyState, mockCards, '2026-09-30');
assert(pillText.startsWith('🎯 今日计划: 0 / 60 词 | 🔥 连续打卡 1 天'));

// Complete Day 2 quota: streak should increment from 1 to 2!
celebrationTriggered = false;
for (let i = 0; i < 60; i++) {
  simulateCardStudy(studyState, mockCards, mockCards[i + 70].id, () => { celebrationTriggered = true; }, '2026-09-30');
}
assert.strictEqual(celebrationTriggered, true);
assert.strictEqual(studyState.daily.streakDays, 2, "streakDays must increment to 2 upon completing consecutive day");

// Transition to Day 3 (2026-10-01): consecutive day
simulateDayTransition(studyState, '2026-10-01');
assert.strictEqual(studyState.daily.streakDays, 2, "streakDays preserved at 2");

// Complete Day 3 quota: streak increments to 3
for (let i = 0; i < 60; i++) {
  simulateCardStudy(studyState, mockCards, mockCards[i + 140].id, null, '2026-10-01');
}
assert.strictEqual(studyState.daily.streakDays, 3);

// Test Missed Day Scenario (Day 4 opened but NOT completed):
simulateDayTransition(studyState, '2026-10-02'); // Day 4 opens
assert.strictEqual(studyState.daily.streakDays, 3, "Day 4 starts with preserved streak of 3");
// User only studies 5 cards on Day 4, does not hit 60 quota
for (let i = 0; i < 5; i++) {
  if (!studyState.daily.todayLearnedIds.includes(mockCards[i].id)) studyState.daily.todayLearnedIds.push(mockCards[i].id);
}
assert.strictEqual(studyState.daily.lastCheckinDate, '2026-10-01', "Checkin date remains Day 3");

// Day 5 arrives (2026-10-03):
simulateDayTransition(studyState, '2026-10-03');
// Because Day 4 was NOT checked in, streak is broken!
assert.strictEqual(studyState.daily.streakDays, 1, "streakDays must reset to 1 because Day 4 check-in was missed");

// Complete Day 5:
for (let i = 0; i < 60; i++) {
  simulateCardStudy(studyState, mockCards, mockCards[i + 200].id, null, '2026-10-03');
}
assert.strictEqual(studyState.daily.streakDays, 1, "Day 5 fresh streak is 1");
assert.strictEqual(studyState.daily.lastCheckinDate, '2026-10-03');

// Test Multi-Day Skip (e.g. skip from 2026-10-03 to 2026-10-07, diffDays > 1)
simulateDayTransition(studyState, '2026-10-07');
assert.strictEqual(studyState.daily.streakDays, 1, "streakDays must reset to 1 after multi-day absence");

// Test Uninitialized State Robustness: empty date string must not cause NaN
let freshState = { daily: { date: '' } };
simulateDayTransition(freshState, '2026-10-08');
assert.strictEqual(freshState.daily.date, '2026-10-08');
assert.strictEqual(freshState.daily.streakDays, 1);
assert(!isNaN(freshState.daily.streakDays), "Must not produce NaN");

console.log('✓ 3. Daily quota accumulation, celebration trigger, consecutive streak preservation, and missed-day streak reset verified.');


// 4. Testing Breakpoint Resume, Plan Switching & Year Advancement
console.log('\n--- 4. Testing Breakpoint Resume, Midway Plan Switching & Year Advancement ---');

// Build queue simulation with breakpoint support
function buildQueueWithBreakpoint(state, allCards) {
  const pool = allCards.filter(c => c.year === state.activeYear);
  if (state.activeFilter === 'all') {
    state.queue = pool.filter(c => !state.masteredIds.has(c.id));
    if (state.queue.length === 0) state.queue = [...pool];
  }

  let resumeIdx = 0;
  if (state.breakpointCardId) {
    const foundIdx = state.queue.findIndex(c => c.id === state.breakpointCardId);
    if (foundIdx >= 0) {
      resumeIdx = foundIdx;
    }
  }
  state.currentIndex = resumeIdx;
}

// Year advancement simulation
function checkYearCompletionAndAdvance(state, allCards) {
  const yearCards = allCards.filter(c => c.year === state.activeYear);
  if (yearCards.length > 0 && yearCards.every(c => state.masteredIds.has(c.id))) {
    state.completedYears.add(state.activeYear);
    const allYears = Array.from(new Set(allCards.map(c => c.year))).sort((a, b) => a - b);
    const nextYear = allYears.find(yr => yr > state.activeYear);
    if (nextYear) {
      state.activeYear = nextYear;
      state.activeScope = 'all';
      state.breakpointCardId = null; // Reset breakpoint for new year
      buildQueueWithBreakpoint(state, allCards);
      return true;
    } else {
      return false; // All years 100% mastered
    }
  }
  return false;
}

let bpState = {
  activeYear: 2007,
  activeScope: 'all',
  activeFilter: 'all',
  queue: [],
  currentIndex: 0,
  breakpointCardId: null,
  masteredIds: new Set(),
  reviewIds: new Set(),
  completedYears: new Set(),
  plan: { mode: 'intensive', customDailyTarget: 50, customDeadline: '', startDate: '2026-10-05' }
};

// 1. Initially at card 0
buildQueueWithBreakpoint(bpState, mockCards);
assert.strictEqual(bpState.currentIndex, 0);
assert.strictEqual(bpState.queue[0].id, '2007-T1-01');

// 2. User masters first 5 cards (2007-T1-01 to 2007-T1-05)
for (let i = 1; i <= 5; i++) {
  bpState.masteredIds.add(`2007-T1-${String(i).padStart(2, '0')}`);
}
// User leaves on card #12 (2007-T1-12) without mastering it
bpState.breakpointCardId = '2007-T1-12';
bpState.reviewIds.add('2007-T1-08');

// 3. Test switching plans midway: strictly preserves startDate, masteredIds, reviewIds, and breakpoint!
function switchPlanMidway(state, newMode, newTarget = null, newDeadline = null, newStartDate = undefined) {
  state.plan.mode = newMode;
  if (newStartDate !== undefined) state.plan.startDate = newStartDate;
  if (newMode === 'custom') {
    if (newTarget) state.plan.customDailyTarget = newTarget;
    if (newDeadline) state.plan.customDeadline = newDeadline;
  }
}
switchPlanMidway(bpState, 'steady');
assert.strictEqual(bpState.plan.mode, 'steady', "Plan mode switched to steady");
assert.strictEqual(bpState.plan.startDate, '2026-10-05', "startDate strictly preserved across plan switch");
assert.strictEqual(bpState.masteredIds.size, 5, "masteredIds strictly preserved");
assert.strictEqual(bpState.reviewIds.has('2007-T1-08'), true, "reviewIds strictly preserved");
assert.strictEqual(bpState.breakpointCardId, '2007-T1-12', "breakpointCardId strictly preserved");

// 4. User reloads or revisits the app next time
buildQueueWithBreakpoint(bpState, mockCards);
// Queue contains remaining unmastered cards (from 06 onward)
assert.strictEqual(bpState.queue.length, 112 - 5);
// Current index must resume directly at 2007-T1-12, NOT card 0!
assert(bpState.currentIndex > 0, "Must not reset to card 0");
assert.strictEqual(bpState.queue[bpState.currentIndex].id, '2007-T1-12', "Must resume at exact breakpoint 2007-T1-12");

// 5. Verify year advancement does NOT trigger prematurely if year is not 100% mastered
assert.strictEqual(checkYearCompletionAndAdvance(bpState, mockCards), false, "Must not advance year while unmastered cards remain");
assert.strictEqual(bpState.activeYear, 2007, "Year must remain 2007");

// 6. Now master all remaining cards of 2007
const year2007Cards = mockCards.filter(c => c.year === 2007);
year2007Cards.forEach(c => bpState.masteredIds.add(c.id));

// Check advancement: 2007 is 100% mastered -> must roll forward to 2008!
const advanced = checkYearCompletionAndAdvance(bpState, mockCards);
assert.strictEqual(advanced, true, "Must advance to next year when 100% mastered");
assert.strictEqual(bpState.activeYear, 2008, "Active year must roll forward to 2008");
assert.strictEqual(bpState.completedYears.has(2007), true, "2007 must be recorded in completedYears");
assert.strictEqual(bpState.currentIndex, 0, "New year starts at card 0");
assert.strictEqual(bpState.queue[0].year, 2008, "Queue must contain 2008 cards");

// 7. Master 2008, 2009, and 2010 sequentially
mockCards.filter(c => c.year === 2008).forEach(c => bpState.masteredIds.add(c.id));
assert.strictEqual(checkYearCompletionAndAdvance(bpState, mockCards), true);
assert.strictEqual(bpState.activeYear, 2009);

mockCards.filter(c => c.year === 2009).forEach(c => bpState.masteredIds.add(c.id));
assert.strictEqual(checkYearCompletionAndAdvance(bpState, mockCards), true);
assert.strictEqual(bpState.activeYear, 2010);

mockCards.filter(c => c.year === 2010).forEach(c => bpState.masteredIds.add(c.id));
// All years mastered!
const finalAdv = checkYearCompletionAndAdvance(bpState, mockCards);
assert.strictEqual(finalAdv, false, "No next year after 2010, marks full victory");
assert.strictEqual(bpState.completedYears.size, 4, "All 4 years recorded as completed");

console.log('✓ 4. Breakpoint protection, midway plan switching, and automatic year roll-forward verified.');

// 5. Check version.json and sw.js
console.log('\n--- 5. Testing Version Alignment across all project files ---');
const verJson = JSON.parse(fs.readFileSync(path.join(__dirname, 'version.json'), 'utf8'));
assert.strictEqual(verJson.version, '1.2.1', 'version.json version mismatch');

const swContent = fs.readFileSync(path.join(__dirname, 'sw.js'), 'utf8');
assert(swContent.includes("const CACHE_VERSION = 'v1.2.1';"), 'sw.js CACHE_VERSION mismatch');

console.log('✓ 5. Version v1.2.1 strictly synchronized across version.json, sw.js, and HTML files.');

console.log('\n===============================================================');
console.log('🎉 ALL PLAN, QUOTA & BREAKPOINT TESTS PASSED WITH 100% SUCCESS!');
console.log('===============================================================');
