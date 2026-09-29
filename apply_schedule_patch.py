# -*- coding: utf-8 -*-
"""
apply_schedule_patch.py
Applies the full Multi-Plan, Daily Quota, Breakpoint Resume, and Year Advancement systems
to index.html and 考研英语刷题卡.html.
"""

import os
import re

def build_full_script():
    return '''    // 考研复习计划方案定义
    const PLAN_PRESETS = {
      steady: {
        id: 'steady',
        name: '稳步精读型',
        icon: '🌿',
        dailyTarget: 35,
        desc: '35 词/天 · 约 1 篇精读/天 · 适合打底细嚼慢咽'
      },
      intensive: {
        id: 'intensive',
        name: '高效强化型',
        icon: '⚡',
        dailyTarget: 60,
        desc: '60 词/天 · 约 2 篇精读/天 · 强化攻坚 (默认推荐)'
      },
      yearly: {
        id: 'yearly',
        name: '整年通刷型',
        icon: '🔥',
        dailyTarget: null, // 动态计算为当前年份总词数
        desc: '1 整年/天 · 高能通刷冲刺 · 考前冲刺全景模考'
      },
      custom: {
        id: 'custom',
        name: '自定义目标型',
        icon: '⚙️',
        dailyTarget: 50,
        desc: '自由设定每日定量或倒计时 · 灵活弹性备考'
      }
    };

    // 应用运行状态
    let state = {
      activeYear: 2010,
      activeScope: 'all', // 'all' (整年通刷) 或 'Text 1', 'Text 2' ...
      activeFilter: 'all', // 词汇分类
      mode: 'word', // 'word' 或 'translate'
      queue: [],
      currentIndex: 0,
      masteredIds: new Set(),
      reviewIds: new Set(),
      isFlipped: false,

      // 断点保护与自动晋级
      breakpointCardId: null,
      completedYears: new Set(),

      // 复习计划体系
      plan: {
        mode: 'intensive', // 'steady' (35), 'intensive' (60), 'yearly', 'custom'
        customDailyTarget: 50,
        customDeadline: ''
      },

      // 每日定量推送与打卡连续记录
      daily: {
        date: '',
        todayLearnedIds: [],
        streakDays: 1,
        lastStudyDate: '',
        lastCheckinDate: null,
        goalCelebrated: false
      }
    };

    // 本地日期辅助函数 (格式: YYYY-MM-DD)
    function getLocalDateString(d = new Date()) {
      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    }

    // 获取当前计划的每日定量目标
    function getDailyTarget(mode) {
      const m = mode || (state.plan && state.plan.mode) || 'intensive';
      if (m === 'steady') return 35;
      if (m === 'intensive') return 60;
      if (m === 'yearly') {
        const yearCards = ALL_CARDS.filter(c => c.year === state.activeYear);
        return Math.max(yearCards.length, 1);
      }
      if (m === 'custom') {
        if (state.plan && state.plan.customDeadline) {
          const today = new Date(getLocalDateString() + 'T00:00:00');
          const targetDate = new Date(state.plan.customDeadline + 'T00:00:00');
          const diffDays = Math.ceil((targetDate.getTime() - today.getTime()) / (1000 * 3600 * 24));
          if (diffDays > 0) {
            const unmastered = ALL_CARDS.filter(c => !state.masteredIds.has(c.id)).length;
            return Math.max(Math.ceil(unmastered / diffDays), 1);
          }
        }
        const val = state.plan && state.plan.customDailyTarget;
        return Math.max(parseInt(val, 10) || 50, 1);
      }
      return 60;
    }

    // 动态测算通关日期 (ETD: Estimated Completion Date)
    function getETDInfo(targetOverride) {
      const unmastered = ALL_CARDS.filter(c => !state.masteredIds.has(c.id)).length;
      if (unmastered === 0) {
        return { unmastered: 0, daysRemaining: 0, etdStr: '已全量通关 🎉' };
      }
      if (state.plan && state.plan.mode === 'custom' && state.plan.customDeadline) {
        const today = new Date(getLocalDateString() + 'T00:00:00');
        const targetDate = new Date(state.plan.customDeadline + 'T00:00:00');
        const diffDays = Math.ceil((targetDate.getTime() - today.getTime()) / (1000 * 3600 * 24));
        if (diffDays > 0) {
          const finishDate = targetDate;
          const etdStr = `${finishDate.getMonth() + 1}月${finishDate.getDate()}日`;
          return { unmastered, daysRemaining: diffDays, etdStr };
        }
      }
      const dailyTarget = targetOverride || getDailyTarget();
      const daysRemaining = Math.ceil(unmastered / Math.max(dailyTarget, 1));
      const finishDate = new Date(Date.now() + daysRemaining * 86400000);
      const etdStr = `${finishDate.getMonth() + 1}月${finishDate.getDate()}日`;
      return { unmastered, daysRemaining, etdStr };
    }

    // 跨天调度与连续打卡保护
    function checkCalendarDayTransition() {
      const todayStr = getLocalDateString();
      if (!state.daily || !state.daily.date) {
        state.daily = {
          date: todayStr,
          todayLearnedIds: [],
          streakDays: 1,
          lastStudyDate: todayStr,
          lastCheckinDate: null,
          goalCelebrated: false
        };
        return;
      }

      if (state.daily.date !== todayStr) {
        const prevDateStr = state.daily.date;
        const prevDate = new Date(prevDateStr + 'T00:00:00');
        const currDate = new Date(todayStr + 'T00:00:00');
        const diffDays = Math.round((currDate.getTime() - prevDate.getTime()) / (1000 * 3600 * 24));

        // 1. 跨自然日：自动重置今日已背词数与完成弹窗状态
        state.daily.todayLearnedIds = [];
        state.daily.goalCelebrated = false;
        state.daily.date = todayStr;

        // 2. 连续打卡保护：
        // 算出昨天日期
        const yesterday = new Date(currDate);
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = getLocalDateString(yesterday);

        // 如果中断超过 1 天未打开应用，或者昨天未完成打卡，重置打卡连续天数为 1
        if (diffDays > 1 || (state.daily.lastCheckinDate && state.daily.lastCheckinDate !== yesterdayStr)) {
          state.daily.streakDays = 1;
        }
        // 如果昨天完成了打卡，streakDays 完好保留

        saveState();
      }
    }

    // 连续打卡记录
    function recordDailyCheckin() {
      const todayStr = getLocalDateString();
      if (!state.daily) checkCalendarDayTransition();

      if (state.daily.lastCheckinDate !== todayStr) {
        const yesterday = new Date();
        yesterday.setDate(yesterday.getDate() - 1);
        const yesterdayStr = getLocalDateString(yesterday);

        if (state.daily.lastCheckinDate === yesterdayStr) {
          state.daily.streakDays = (state.daily.streakDays || 1) + 1;
        } else {
          state.daily.streakDays = 1;
        }
        state.daily.lastCheckinDate = todayStr;
        saveState();
      }
    }

    // 记录卡片学习进度与每日定量达成检测
    function recordDailyProgress(cardId) {
      if (!state.daily) checkCalendarDayTransition();

      const todayStr = getLocalDateString();
      if (state.daily.date !== todayStr) {
        checkCalendarDayTransition();
      }

      if (cardId && !state.daily.todayLearnedIds.includes(cardId)) {
        state.daily.todayLearnedIds.push(cardId);
      }
      state.daily.lastStudyDate = todayStr;

      // 达成今日定量目标检测
      const target = getDailyTarget();
      if (state.daily.todayLearnedIds.length >= target && !state.daily.goalCelebrated) {
        state.daily.goalCelebrated = true;
        recordDailyCheckin();
        openDailyGoalModal();
      }
    }

    // 更新顶部计划状态胶囊
    function updateHeaderPlanPill() {
      const pill = document.getElementById('headerPlanPill');
      if (!pill) return;

      const todayCount = state.daily && state.daily.todayLearnedIds ? state.daily.todayLearnedIds.length : 0;
      const target = getDailyTarget();
      const streak = state.daily ? state.daily.streakDays : 1;
      const { unmastered, etdStr } = getETDInfo();

      const etdPart = unmastered === 0 ? '预计 已全量通关 🎉' : `预计 ${etdStr} 全量通关`;
      pill.textContent = `🎯 今日计划: ${todayCount} / ${target} 词 | 🔥 连续打卡 ${streak} 天 | ${etdPart}`;

      // 同步更新侧边抽屉内的计划概览
      const drawerPlanName = document.getElementById('drawerPlanName');
      const drawerPlanDesc = document.getElementById('drawerPlanDesc');
      if (drawerPlanName && drawerPlanDesc) {
        const curPlan = PLAN_PRESETS[state.plan.mode] || PLAN_PRESETS.intensive;
        let targetLabel = `${target}词/天`;
        if (state.plan.mode === 'yearly') {
          targetLabel = `${target}词(全年)`;
        } else if (state.plan.mode === 'custom' && state.plan.customDeadline) {
          targetLabel = `${target}词/天 · 冲刺至${state.plan.customDeadline}`;
        }
        drawerPlanName.textContent = `${curPlan.icon} ${curPlan.name} (${targetLabel})`;
        drawerPlanDesc.textContent = `${etdPart} · 连续打卡 ${streak} 天`;
      }
    }

    // 每日定量目标达成弹窗
    function openDailyGoalModal() {
      const modal = document.getElementById('dailyGoalModal');
      if (!modal) return;
      const todayCount = state.daily.todayLearnedIds.length;
      const target = getDailyTarget();
      const streak = state.daily.streakDays;
      const { unmastered, etdStr } = getETDInfo();

      const summary = document.getElementById('dailyGoalSummaryText');
      if (summary) {
        const etdPart = unmastered === 0 ? '已全量通关 🎉' : `预计 ${etdStr} 全量通关`;
        summary.innerHTML = `今日已攻克 <strong>${todayCount} / ${target}</strong> 词 · 连续打卡 <strong>${streak}</strong> 天！<br>${etdPart}`;
      }
      modal.style.display = 'flex';
      if ('vibrate' in navigator) navigator.vibrate([20, 50, 20]);
    }

    function finishTodayCheckin() {
      const modal = document.getElementById('dailyGoalModal');
      if (modal) modal.style.display = 'none';
      showToast(`☕ 今日打卡圆满成功！已连续打卡 ${state.daily.streakDays} 天，劳逸结合，明天见！`, 3500);
    }

    function continueStudying() {
      const modal = document.getElementById('dailyGoalModal');
      if (modal) modal.style.display = 'none';
      showToast('💪 保持势头，继续挑战！超额背诵将持续累积今日战果！', 2500);
    }

    // 多套复习计划选择弹窗
    let tempSelectedPlanMode = 'intensive';

    function openPlanModal() {
      const modal = document.getElementById('planModal');
      if (!modal) return;
      tempSelectedPlanMode = state.plan ? state.plan.mode : 'intensive';
      const customInput = document.getElementById('customTargetInput');
      if (customInput && state.plan && state.plan.customDailyTarget) {
        customInput.value = state.plan.customDailyTarget;
      }
      const customDeadlineInput = document.getElementById('customDeadlineInput');
      if (customDeadlineInput && state.plan && state.plan.customDeadline) {
        customDeadlineInput.value = state.plan.customDeadline;
      }
      const customBox = document.getElementById('customPlanInputBox');
      if (customBox) {
        customBox.style.display = tempSelectedPlanMode === 'custom' ? 'block' : 'none';
      }
      renderPlanOptionsList();
      modal.style.display = 'flex';
    }

    function closePlanModal() {
      const modal = document.getElementById('planModal');
      if (modal) modal.style.display = 'none';
    }

    function selectPlanMode(mode) {
      tempSelectedPlanMode = mode;
      const customBox = document.getElementById('customPlanInputBox');
      if (customBox) {
        customBox.style.display = mode === 'custom' ? 'block' : 'none';
      }
      renderPlanOptionsList();
      updatePlanModalFooter();
    }

    function onCustomTargetChange() {
      const deadlineInput = document.getElementById('customDeadlineInput');
      const hint = document.getElementById('customDeadlineHint');
      if (deadlineInput) deadlineInput.value = '';
      if (hint) hint.textContent = '💡 自定义每日背词目标，系统将自动测算通关日期。';
      updatePlanModalFooter();
      renderPlanOptionsList();
    }

    function onCustomDeadlineChange() {
      const deadlineInput = document.getElementById('customDeadlineInput');
      const targetInput = document.getElementById('customTargetInput');
      const hint = document.getElementById('customDeadlineHint');
      if (!deadlineInput || !targetInput) return;

      const deadlineVal = deadlineInput.value;
      if (!deadlineVal) {
        if (hint) hint.textContent = '💡 可直接指定每日背词数，或选择考研倒计时截止日自动推算。';
        updatePlanModalFooter();
        renderPlanOptionsList();
        return;
      }

      const today = new Date(getLocalDateString() + 'T00:00:00');
      const targetDate = new Date(deadlineVal + 'T00:00:00');
      const diffDays = Math.ceil((targetDate.getTime() - today.getTime()) / (1000 * 3600 * 24));
      const unmastered = ALL_CARDS.filter(c => !state.masteredIds.has(c.id)).length;

      if (diffDays <= 0) {
        if (hint) hint.innerHTML = '⚠️ <span style="color:#ef4444;">截止日期不能早于或等于今天，已恢复默认定量。</span>';
        deadlineInput.value = '';
      } else {
        const calculatedTarget = Math.max(Math.ceil(unmastered / diffDays), 1);
        targetInput.value = calculatedTarget;
        if (hint) hint.innerHTML = `🎯 距目标日尚余 <strong>${diffDays}</strong> 天，为全量通关建议每日攻克 <strong>${calculatedTarget}</strong> 词。`;
      }
      updatePlanModalFooter();
      renderPlanOptionsList();
    }

    function renderPlanOptionsList() {
      const container = document.getElementById('planOptionsList');
      if (!container) return;

      const unmastered = ALL_CARDS.filter(c => !state.masteredIds.has(c.id)).length;
      const modes = ['steady', 'intensive', 'yearly', 'custom'];

      let html = '';
      modes.forEach(m => {
        const p = PLAN_PRESETS[m];
        const isAct = tempSelectedPlanMode === m ? 'active' : '';
        let target = 0;
        let descText = p.desc;

        if (m === 'steady') {
          target = 35;
        } else if (m === 'intensive') {
          target = 60;
        } else if (m === 'yearly') {
          target = Math.max(ALL_CARDS.filter(c => c.year === state.activeYear).length, 1);
        } else if (m === 'custom') {
          const inputEl = document.getElementById('customTargetInput');
          target = inputEl ? (parseInt(inputEl.value, 10) || 50) : (state.plan.customDailyTarget || 50);
          const deadlineInput = document.getElementById('customDeadlineInput');
          const dVal = deadlineInput ? deadlineInput.value : (state.plan && state.plan.customDeadline);
          if (dVal) {
            descText = `目标日 ${dVal} · 倒推每日 ${target} 词 · 弹性备考`;
          }
        }

        let etdText = '';
        if (unmastered === 0) {
          etdText = '已全量通关 🎉';
        } else {
          let finishDate;
          let days;
          if (m === 'custom') {
            const deadlineInput = document.getElementById('customDeadlineInput');
            const dVal = deadlineInput ? deadlineInput.value : (state.plan && state.plan.customDeadline);
            if (dVal && new Date(dVal + 'T00:00:00') > new Date(getLocalDateString() + 'T00:00:00')) {
              finishDate = new Date(dVal + 'T00:00:00');
              days = Math.ceil((finishDate.getTime() - new Date(getLocalDateString() + 'T00:00:00').getTime()) / 86400000);
            }
          }
          if (!finishDate) {
            days = Math.ceil(unmastered / Math.max(target, 1));
            finishDate = new Date(Date.now() + days * 86400000);
          }
          etdText = `预计 ${finishDate.getMonth() + 1}月${finishDate.getDate()}日 全量通关 (${days}天)`;
        }

        const badgeText = m === 'intensive' ? '<span class="plan-card-badge">推荐</span>' : '';
        html += `
          <div class="plan-card ${isAct}" onclick="selectPlanMode('${m}')">
            <div class="plan-card-header">
              <span>${p.icon} ${p.name}</span>
              ${badgeText}
            </div>
            <div class="plan-card-desc">${descText}</div>
            <div class="plan-card-etd">⏱️ ${etdText}</div>
          </div>
        `;
      });

      container.innerHTML = html;
      updatePlanModalFooter();
    }

    function updatePlanModalFooter() {
      const unmastered = ALL_CARDS.filter(c => !state.masteredIds.has(c.id)).length;
      let target = getDailyTarget(tempSelectedPlanMode);
      if (tempSelectedPlanMode === 'custom') {
        const inputEl = document.getElementById('customTargetInput');
        if (inputEl) target = parseInt(inputEl.value, 10) || 50;
      }

      const remainingEl = document.getElementById('planModalRemainingText');
      if (remainingEl) remainingEl.textContent = `剩余待攻克：${unmastered} 词`;

      const footerETD = document.getElementById('planModalFooterETD');
      if (footerETD) {
        if (unmastered === 0) {
          footerETD.textContent = '已全量通关 🎉';
        } else {
          let finishDate;
          if (tempSelectedPlanMode === 'custom') {
            const deadlineInput = document.getElementById('customDeadlineInput');
            const dVal = deadlineInput ? deadlineInput.value : (state.plan && state.plan.customDeadline);
            if (dVal && new Date(dVal + 'T00:00:00') > new Date(getLocalDateString() + 'T00:00:00')) {
              finishDate = new Date(dVal + 'T00:00:00');
            }
          }
          if (!finishDate) {
            const days = Math.ceil(unmastered / Math.max(target, 1));
            finishDate = new Date(Date.now() + days * 86400000);
          }
          footerETD.textContent = `预计 ${finishDate.getMonth() + 1}月${finishDate.getDate()}日 全量通关`;
        }
      }
    }

    function saveSelectedPlan() {
      state.plan.mode = tempSelectedPlanMode;
      if (tempSelectedPlanMode === 'custom') {
        const inputEl = document.getElementById('customTargetInput');
        if (inputEl) {
          state.plan.customDailyTarget = Math.max(parseInt(inputEl.value, 10) || 50, 1);
        }
        const deadlineEl = document.getElementById('customDeadlineInput');
        state.plan.customDeadline = deadlineEl ? deadlineEl.value : '';
      }
      saveState();
      updateHeaderPlanPill();
      closePlanModal();

      const curPlan = PLAN_PRESETS[state.plan.mode] || PLAN_PRESETS.intensive;
      const { etdStr, unmastered } = getETDInfo();
      const etdPart = unmastered === 0 ? '已全量通关 🎉' : `预计 ${etdStr} 全量通关`;
      showToast(`🎯 已切换为「${curPlan.name}」！${etdPart}`, 3000);
    }

    // 检查当前年份是否已 100% 掌握并自动晋级到下一年
    function checkYearCompletionAndAdvance() {
      const yearCards = ALL_CARDS.filter(c => c.year === state.activeYear);
      if (yearCards.length > 0 && yearCards.every(c => state.masteredIds.has(c.id))) {
        state.completedYears.add(state.activeYear);
        const allYears = Array.from(new Set(ALL_CARDS.map(c => c.year))).sort((a, b) => a - b);
        const nextYear = allYears.find(yr => yr > state.activeYear);
        if (nextYear) {
          const oldYear = state.activeYear;
          showToast(`🏆 恭喜！${oldYear} 年真题已 100% 全部掌握！自动晋级至 ${nextYear} 年真题！`, 4000);
          state.activeYear = nextYear;
          state.activeScope = 'all';
          state.breakpointCardId = null; // 切换新一年，重置断点到新年起始
          saveState();
          renderYearBar();
          renderScopeBar();
          buildQueue();
          return true;
        } else {
          showToast('🏆 壮举！所有年份考研英语真题已 100% 全量斩获！', 4000);
          return false;
        }
      }
      return false;
    }

    // 从本地存储还原进度
    function loadSavedState() {
      try {
        const saved = localStorage.getItem('kaoyan_cards_state');
        if (saved) {
          const parsed = JSON.parse(saved);
          state.masteredIds = new Set(parsed.masteredIds || []);
          state.reviewIds = new Set(parsed.reviewIds || []);
          state.completedYears = new Set(parsed.completedYears || []);
          if (parsed.activeYear) state.activeYear = parsed.activeYear;
          if (parsed.activeScope) state.activeScope = parsed.activeScope;
          if (parsed.mode && (parsed.mode === 'word' || parsed.mode === 'translate' || parsed.mode === 'cloze')) {
            state.mode = (parsed.mode === 'cloze' || parsed.mode === 'translate') ? 'translate' : 'word';
          }
          if (parsed.breakpointCardId) state.breakpointCardId = parsed.breakpointCardId;

          if (parsed.plan) {
            state.plan = Object.assign({ mode: 'intensive', customDailyTarget: 50, customDeadline: '' }, parsed.plan);
          }
          if (parsed.daily) {
            state.daily = Object.assign({
              date: getLocalDateString(),
              todayLearnedIds: [],
              streakDays: 1,
              lastStudyDate: getLocalDateString(),
              lastCheckinDate: null,
              goalCelebrated: false
            }, parsed.daily);
            if (!Array.isArray(state.daily.todayLearnedIds)) {
              state.daily.todayLearnedIds = [];
            }
          }
        }
      } catch (e) {
        console.error('loadSavedState error:', e);
      }

      // 跨天调度检查与连续打卡保护
      checkCalendarDayTransition();

      // 自动同步已 100% 掌握的年份到 completedYears
      const allYears = Array.from(new Set(ALL_CARDS.map(c => c.year))).sort((a, b) => a - b);
      allYears.forEach(yr => {
        const yCards = ALL_CARDS.filter(c => c.year === yr);
        if (yCards.length > 0 && yCards.every(c => state.masteredIds.has(c.id))) {
          state.completedYears.add(yr);
        }
      });

      // 如果当前保存的年份已经 100% 全部掌握，自动定位到首个尚未全量通关的年份
      const currentYearCards = ALL_CARDS.filter(c => c.year === state.activeYear);
      if (currentYearCards.length > 0 && currentYearCards.every(c => state.masteredIds.has(c.id))) {
        const uncompletedYear = allYears.find(yr => {
          const yCards = ALL_CARDS.filter(c => c.year === yr);
          return yCards.length > 0 && !yCards.every(c => state.masteredIds.has(c.id));
        });
        if (uncompletedYear) {
          state.activeYear = uncompletedYear;
          state.activeScope = 'all';
          state.breakpointCardId = null;
        }
      }
    }

    function saveState() {
      try {
        localStorage.setItem('kaoyan_cards_state', JSON.stringify({
          activeYear: state.activeYear,
          activeScope: state.activeScope,
          mode: state.mode,
          masteredIds: Array.from(state.masteredIds),
          reviewIds: Array.from(state.reviewIds),
          completedYears: Array.from(state.completedYears),
          breakpointCardId: state.breakpointCardId,
          plan: state.plan,
          daily: state.daily
        }));
      } catch (e) {
        console.error('saveState error:', e);
      }
    }

    // 根据年份与篇章过滤卡片
    function getScopedCards() {
      return ALL_CARDS.filter(c => {
        if (c.year !== state.activeYear) return false;
        if (state.activeScope === 'all') return true; // 整年通刷
        return c.text === state.activeScope;
      });
    }

    // 构建复习队列 (支持断点保护恢复)
    function buildQueue() {
      const pool = getScopedCards();

      if (state.activeFilter === 'all') {
        state.queue = pool.filter(c => !state.masteredIds.has(c.id));
        if (state.queue.length === 0) state.queue = [...pool];
      } else if (state.activeFilter === 'review') {
        state.queue = pool.filter(c => state.reviewIds.has(c.id));
        if (state.queue.length === 0) {
          alert("太棒了！当前范围内没有任何标记为待攻克的错题！");
          setFilter('all');
          return;
        }
      } else {
        state.queue = pool.filter(c => c.category === state.activeFilter);
      }

      // 断点保护：优先从已保存的未掌握断点继续，绝不意外重置到卡片 0
      let resumeIdx = 0;
      if (state.breakpointCardId) {
        const foundIdx = state.queue.findIndex(c => c.id === state.breakpointCardId);
        if (foundIdx >= 0) {
          resumeIdx = foundIdx;
        }
      }
      state.currentIndex = resumeIdx;

      updateHeaderScopeDisplay();
      renderCategoryChips();
      updateHeaderPlanPill();
      updateUI();
    }

    function updateHeaderScopeDisplay() {
      const scopeLabel = state.activeScope === 'all' ? `${state.activeYear} 全年复习` : `${state.activeYear} · ${state.activeScope}`;
      document.getElementById('headerScopePill').textContent = scopeLabel + ' ▼';
      document.getElementById('drawerCurrentYear').textContent = `当前：${state.activeYear}年 (${state.activeScope === 'all' ? '整年复习' : state.activeScope})`;
      
      // 更新 scope bar 选中状态
      document.querySelectorAll('.scope-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.scope === state.activeScope);
      });
    }

    // 单词纯净提取
    function getCleanWord(card) {
      if (!card || !card.word) return '';
      let w = card.word.replace(/\\s*[\\(（][^()（）]*[\\)）]\\s*/g, ' ').trim();
      return w || card.word;
    }

    function getCleanDef(card) {
      if (!card || !card.def) return '';
      let d = card.def;
      d = d.replace(/[\\(（](封为)[\\)）]/g, '$1');
      d = d.replace(/[\\(（](不)[\\)）]/g, '$1');
      d = d.replace(/[\\(（](非)[\\)）]/g, '$1');
      d = d.replace(/[\\(（](原为)[\\)）]/g, '$1');
      d = d.replace(/[\\(（](几乎)[\\)）]/g, '$1');
      d = d.replace(/[\\(（](原判)[\\)）]/g, '$1');
      d = d.replace(/\\s*[\\(（][^()（）]*[\\)）]\\s*/g, ' ');
      d = d.replace(/\\s*[;；]\\s*/g, '；');
      d = d.replace(/\\s*[,，]\\s*/g, '，');
      d = d.replace(/\\s*[、]\\s*/g, '、');
      d = d.replace(/\\s*[;；,，、]\\s*$/g, '');
      return d.replace(/\\s+/g, ' ').trim();
    }

    function getExamPoint(card) {
      if (!card) return '';
      let tag = card.noteTag || '';
      if (tag && !tag.startsWith('★')) {
        tag = '★ ' + tag;
      }
      return tag;
    }

    // 渲染卡片 (同步断点与计划进度)
    function renderCurrentCard() {
      const card = state.queue[state.currentIndex];
      const flashcard = document.getElementById('flashcard');
      
      flashcard.classList.remove('flipped');
      state.isFlipped = false;

      if (!card) {
        document.getElementById('finishModal').style.display = 'flex';
        document.getElementById('finishSummaryText').textContent = `已经攻关 ${state.activeYear} 年 ${state.activeScope === 'all' ? '全部4篇阅读' : state.activeScope} 核心考点！`;
        updateHeaderPlanPill();
        return;
      }
      document.getElementById('finishModal').style.display = 'none';

      // 记录断点卡片 ID
      state.breakpointCardId = card.id;

      const cleanWord = getCleanWord(card);
      const cleanDef = getCleanDef(card);
      const examPoint = getExamPoint(card);

      // 正面渲染
      document.getElementById('cardCategory').textContent = card.category;
      document.getElementById('cardSource').textContent = `${card.year} · ${card.text}`;
      document.getElementById('frontWord').textContent = cleanWord;
      
      const frontSent = document.getElementById('frontTranslateSentence') || document.getElementById('frontClozeSentence');
      if (frontSent) frontSent.innerHTML = card.sentence || card.sentencePlain;

      // 背面渲染
      document.getElementById('backCategory').textContent = card.category;
      const testedWordInline = document.getElementById('backTestedWord');
      if (testedWordInline) testedWordInline.textContent = `· ${cleanWord}`;
      document.getElementById('backDef').textContent = cleanDef;
      
      const examBox = document.getElementById('backExamBox');
      const tagEl = document.getElementById('backNoteTag');
      if (examPoint) {
        if (examBox) examBox.style.display = 'block';
        if (tagEl) {
          tagEl.style.display = 'block';
          tagEl.textContent = examPoint;
        }
      } else {
        if (examBox) examBox.style.display = 'none';
        if (tagEl) tagEl.style.display = 'none';
      }

      document.getElementById('backSentenceOrigin').textContent = `${card.year} ${card.text}`;
      document.getElementById('backSentence').innerHTML = card.sentence;
      document.getElementById('backTranslation').textContent = card.translation;

      // 模式2 (原句翻译) 专属：翻转卡片置顶呈现真题参考译文
      const heroTransBox = document.getElementById('backTranslateHeroBox');
      const heroTransText = document.getElementById('backHeroTranslation');
      const backTransHeading = document.getElementById('backTransHeading');
      const backTranslation = document.getElementById('backTranslation');
      const backSentenceBlock = document.getElementById('backSentenceBlock');
      
      const isTranslateMode = (state.mode === 'translate' || state.mode === 'cloze');
      if (isTranslateMode) {
        if (heroTransBox) heroTransBox.style.display = 'block';
        if (heroTransText) heroTransText.textContent = card.translation;
        if (backTransHeading) backTransHeading.style.display = 'none';
        if (backTranslation) backTranslation.style.display = 'none';
        if (backSentenceBlock) backSentenceBlock.style.display = 'none';
      } else {
        if (heroTransBox) heroTransBox.style.display = 'none';
        if (backTransHeading) backTransHeading.style.display = 'flex';
        if (backTranslation) backTranslation.style.display = 'block';
        if (backSentenceBlock) backSentenceBlock.style.display = 'block';
      }

      // 进度统计
      const pool = getScopedCards();
      const masteredInScope = pool.filter(c => state.masteredIds.has(c.id)).length;
      const reviewInScope = pool.filter(c => state.reviewIds.has(c.id)).length;

      const progressPercent = ((state.currentIndex) / Math.max(state.queue.length, 1)) * 100;
      document.getElementById('progressBar').style.width = `${progressPercent}%`;
      document.getElementById('counterText').textContent = `卡片: ${state.currentIndex + 1} / ${state.queue.length}`;
      document.getElementById('masteredCount').textContent = `✓ ${masteredInScope} 掌握`;
      document.getElementById('needReviewCount').textContent = `✕ ${reviewInScope} 待攻克`;

      updateHeaderPlanPill();
    }

    // 翻转卡片
    function toggleFlip() {
      const flashcard = document.getElementById('flashcard');
      state.isFlipped = !state.isFlipped;
      if (state.isFlipped) {
        flashcard.classList.add('flipped');
      } else {
        flashcard.classList.remove('flipped');
      }
      if ('vibrate' in navigator) navigator.vibrate(10);
    }

    // 卡片反馈交互 (认识、模糊、不认识)
    function handleCardAction(action) {
      const currentCard = state.queue[state.currentIndex];
      if (!currentCard) return;

      if ('vibrate' in navigator) navigator.vibrate(15);

      // 记录每日定量背诵卡片
      recordDailyProgress(currentCard.id);

      if (action === 'pass') {
        state.masteredIds.add(currentCard.id);
        state.reviewIds.delete(currentCard.id);
        state.queue.splice(state.currentIndex, 1);

        // 检查当前年份是否 100% 全部掌握并自动晋级到下一年
        const advanced = checkYearCompletionAndAdvance();
        if (advanced) {
          saveState();
          return;
        }
      } else if (action === 'fuzzy') {
        state.reviewIds.add(currentCard.id);
        state.masteredIds.delete(currentCard.id);
        const cardToReinsert = state.queue.splice(state.currentIndex, 1)[0];
        const newPos = Math.min(state.currentIndex + 3, state.queue.length);
        state.queue.splice(newPos, 0, cardToReinsert);
      } else if (action === 'fail') {
        state.reviewIds.add(currentCard.id);
        state.masteredIds.delete(currentCard.id);
        const cardToReinsert = state.queue.splice(state.currentIndex, 1)[0];
        state.queue.push(cardToReinsert);
      }

      if (state.queue.length === 0 || state.currentIndex >= state.queue.length) {
        if (state.queue.length > 0) {
          state.currentIndex = 0;
        } else {
          state.breakpointCardId = null;
          saveState();
          document.getElementById('finishModal').style.display = 'flex';
          updateHeaderPlanPill();
          return;
        }
      }

      // 保存断点
      if (state.queue.length > 0) {
        state.breakpointCardId = state.queue[state.currentIndex].id;
      }
      saveState();

      renderCurrentCard();
      updateHeaderPlanPill();
    }

    // 发音
    function playPronunciation() {
      const currentCard = state.queue[state.currentIndex];
      if (!currentCard) return;
      speakText(getCleanWord(currentCard));
    }

    function playSentence() {
      const currentCard = state.queue[state.currentIndex];
      if (!currentCard) return;
      speakText(currentCard.sentencePlain);
    }

    function speakText(text) {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'en-US';
        utterance.rate = 0.9;
        window.speechSynthesis.speak(utterance);
      }
    }

    // 模式切换 (词汇·短语速记 vs 真题原句翻译)
    function setMode(mode) {
      state.mode = (mode === 'cloze' || mode === 'translate') ? 'translate' : 'word';
      saveState();
      document.querySelectorAll('.mode-tab').forEach(el => el.classList.remove('active'));

      const wordTab = document.getElementById('modeWord');
      const transTab = document.getElementById('modeTranslate') || document.getElementById('modeCloze');
      const wordView = document.getElementById('frontWordView');
      const transView = document.getElementById('frontTranslateView') || document.getElementById('frontClozeView');
      const flipHintText = document.getElementById('frontFlipHintText');

      if (state.mode === 'word') {
        if (wordTab) wordTab.classList.add('active');
        if (wordView) wordView.style.display = 'block';
        if (transView) transView.style.display = 'none';
        if (flipHintText) flipHintText.textContent = '👆 点击卡片翻转查看释义与考点讲解';
      } else {
        if (transTab) transTab.classList.add('active');
        if (wordView) wordView.style.display = 'none';
        if (transView) transView.style.display = 'block';
        if (flipHintText) flipHintText.textContent = '👆 点击卡片翻转查看参考译文与考点讲解';
      }
      renderCurrentCard();
    }

    // 分类筛选切换
    function setFilter(filter) {
      state.activeFilter = filter;
      document.querySelectorAll('.tag-chip').forEach(el => {
        el.classList.toggle('active', el.dataset.filter === filter);
      });
      buildQueue();
    }

    // 切换年份
    function setYear(year) {
      state.activeYear = year;
      state.activeScope = 'all'; // 默认进入整年通刷
      // 如果断点卡片不是当前年份的，重置断点以重新按该年份起始
      if (state.breakpointCardId) {
        const bpCard = ALL_CARDS.find(c => c.id === state.breakpointCardId);
        if (!bpCard || bpCard.year !== year) {
          state.breakpointCardId = null;
        }
      }
      saveState();
      renderYearBar();
      renderScopeBar();
      buildQueue();
    }

    function renderYearBar() {
      const container = document.getElementById('yearBar');
      const years = Array.from(new Set(ALL_CARDS.map(c => c.year))).sort((a, b) => a - b);
      if (container) {
        container.innerHTML = years.map(yr => {
          const isCompleted = state.completedYears && state.completedYears.has(yr);
          const check = isCompleted ? ' ✓' : '';
          return `<div class="year-btn ${yr === state.activeYear ? 'active' : ''}" data-year="${yr}" onclick="setYear(${yr})">${yr} 年${check}</div>`;
        }).join('');
      }
      
      const drawerContainer = document.getElementById('drawerYearButtons');
      if (drawerContainer) {
        drawerContainer.innerHTML = years.map(yr => {
          const isCompleted = state.completedYears && state.completedYears.has(yr);
          const check = isCompleted ? ' ✓' : '';
          return `<button class="scope-btn ${yr === state.activeYear ? 'active' : ''}" style="flex:1; min-width:60px;" onclick="setYear(${yr}); closeDrawer();">${yr}年${check}</button>`;
        }).join('');
      }
    }

    // 动态渲染篇章选择条 (包含真实词数统计及待录入防误触)
    function renderScopeBar() {
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
    }

    // 动态渲染考点分类栏 (统计当前范围内的真实词数)
    function renderCategoryChips() {
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
    }

    // 篇章范围切换 (整年通刷 vs 单篇精刷)
    function setScope(scope) {
      if (scope !== 'all') {
        const hasCards = ALL_CARDS.some(c => c.year === state.activeYear && c.text === scope);
        if (!hasCards) {
          alert(`提示：${state.activeYear} 年 ${scope} 的知识点图片尚未录入，待拍摄上传后会自动解锁！目前请继续复习其他篇章或整年通刷。`);
          return;
        }
      }
      state.activeScope = scope;
      if (state.breakpointCardId) {
        const bpCard = ALL_CARDS.find(c => c.id === state.breakpointCardId);
        if (!bpCard || (scope !== 'all' && bpCard.text !== scope)) {
          state.breakpointCardId = null;
        }
      }
      saveState();
      renderScopeBar();
      buildQueue();
    }

    // 切换年份提示
    function switchYearPrompt() {
      const years = Array.from(new Set(ALL_CARDS.map(c => c.year))).sort();
      const input = prompt(`请输入要复习的年份 (当前已录入年份: ${years.join(', ')}):`, state.activeYear);
      if (input && years.includes(parseInt(input))) {
        setYear(parseInt(input));
        closeDrawer();
      } else if (input) {
        alert(`年份 ${input} 尚未录入笔记图片。后续提供照片后即可解锁！`);
      }
    }

    // 随机打乱
    function shuffleCurrentQueue() {
      for (let i = state.queue.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [state.queue[i], state.queue[j]] = [state.queue[j], state.queue[i]];
      }
      state.currentIndex = 0;
      if (state.queue.length > 0) {
        state.breakpointCardId = state.queue[0].id;
      }
      closeDrawer();
      renderCurrentCard();
    }

    // 导出为 Anki 格式
    function exportToAnki() {
      const pool = getScopedCards();
      let tsv = "#separator:Tab\\n#html:true\\n#tags column:5\\n";
      pool.forEach(c => {
        const cleanW = getCleanWord(c);
        const cleanD = getCleanDef(c);
        const note = getExamPoint(c);
        const front = `<div style='font-size:24px; font-weight:bold;'>${cleanW}</div><div style='color:#666; margin-top:8px;'>${c.category} · ${c.year} ${c.text}</div>`;
        const back = `<div style='font-size:18px; color:#4f46e5; font-weight:bold;'>【核心释义】${cleanD}</div>` +
                     (note ? `<div style='background:#fef3c7; color:#b45309; padding:4px 10px; border-radius:6px; display:inline-block; margin-top:8px; font-weight:bold; font-size:13px;'>【考点讲解】${note}</div>` : '') +
                     `<hr style='margin:14px 0; border:none; border-top:1px solid #e2e8f0;'><div style='line-height:1.6;'>${c.sentence}</div><div style='color:#64748b; margin-top:8px; font-size:14px;'>${c.translation}</div>`;
        tsv += `${cleanW}\\t${cleanD}\\t${front}\\t${back}\\t考研英语::${c.year}::${c.text}\\n`;
      });

      const blob = new Blob([tsv], { type: 'text/tab-separated-values;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `考研英语真题闪卡_${state.activeYear}_${state.activeScope}.tsv`;
      a.click();
      URL.revokeObjectURL(url);
      closeDrawer();
      showToast('🎉 Anki 卡片集已导出！包含【核心释义】与【考点讲解】双板块！');
    }

    // 重置掌握状态
    function resetScopeMastered() {
      if (confirm(`确定要重置 ${state.activeYear} 年 (${state.activeScope === 'all' ? '整年' : state.activeScope}) 的掌握状态吗？`)) {
        const pool = getScopedCards();
        pool.forEach(c => {
          state.masteredIds.delete(c.id);
          state.reviewIds.delete(c.id);
        });
        if (state.completedYears) state.completedYears.delete(state.activeYear);
        state.breakpointCardId = null;
        saveState();
        closeDrawer();
        buildQueue();
        showToast('已重置当前范围的背诵记录！');
      }
    }

    // 重新背诵当前范围
    function restartQueue() {
      const pool = getScopedCards();
      state.queue = [...pool];
      state.currentIndex = 0;
      if (state.queue.length > 0) {
        state.breakpointCardId = state.queue[0].id;
      }
      document.getElementById('finishModal').style.display = 'none';
      renderCurrentCard();
      updateHeaderPlanPill();
    }

    // 抽屉与界面控制
    function openDrawer() {
      updateHeaderPlanPill();
      document.getElementById('drawerOverlay').style.display = 'block';
      document.getElementById('drawer').classList.add('open');
    }

    function closeDrawer() {
      document.getElementById('drawerOverlay').style.display = 'none';
      document.getElementById('drawer').classList.remove('open');
    }

    function toggleTheme() {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('kaoyan_cards_theme', next);
      document.getElementById('themeBtn').textContent = next === 'dark' ? '☀️' : '🌙';
    }

    function showToast(msg, duration = 2500) {
      const toast = document.getElementById('toast');
      toast.textContent = msg;
      toast.style.display = 'block';
      setTimeout(() => {
        toast.style.display = 'none';
      }, duration);
    }

    // 键盘快捷键监听
    document.addEventListener('keydown', (e) => {
      // 弹窗打开时不响应快捷键
      if (document.getElementById('planModal') && document.getElementById('planModal').style.display === 'flex') return;
      if (document.getElementById('dailyGoalModal') && document.getElementById('dailyGoalModal').style.display === 'flex') return;
      if (document.getElementById('finishModal') && document.getElementById('finishModal').style.display === 'flex') return;

      if (e.code === 'Space') {
        e.preventDefault();
        toggleFlip();
      } else if (e.code === 'Digit1' || e.code === 'Numpad1') {
        handleCardAction('fail');
      } else if (e.code === 'Digit2' || e.code === 'Numpad2') {
        handleCardAction('fuzzy');
      } else if (e.code === 'Digit3' || e.code === 'Numpad3') {
        handleCardAction('pass');
      }
    });

    // 初始化运行
    window.onload = () => {
      // 尝试装载 OTA 缓存题库
      initOTACards();

      // 恢复主题设置
      const savedTheme = localStorage.getItem('kaoyan_cards_theme');
      if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.getElementById('themeBtn').textContent = savedTheme === 'dark' ? '☀️' : '🌙';
      }

      loadSavedState();

      // 模式 Tab 初始化高亮
      if (state.mode === 'translate') {
        setMode('translate');
      } else {
        setMode('word');
      }

      renderYearBar();
      renderScopeBar();
      buildQueue();
      updateHeaderPlanPill();
      registerPWA();

      // 在线时安静执行 OTA 检查
      if (navigator.onLine) {
        checkOTAUpdate();
      }
      window.addEventListener('online', () => {
        showToast('🌐 网络已恢复，正在同步最新题库...', 2000);
        checkOTAUpdate(true);
      });

      // 监听前后台切回，自动检查跨天打卡状态
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
          checkCalendarDayTransition();
          updateHeaderPlanPill();
        }
      });
    };

    function updateUI() {
      renderCurrentCard();
    }'''

def patch_file(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update Version in HTML
    html = re.sub(r"const APP_VERSION = '.*?';", "const APP_VERSION = '1.2.0';", html)
    html = re.sub(r'题库版本：v.*? \(', '题库版本：v1.2.0 (', html)

    # 2. Update Theme Variables: ensure --primary-light contrast
    if '--primary-light: rgba(99, 102, 241, 0.18)' not in html:
        html = html.replace(
            '[data-theme="dark"] {\n      --bg: #0b0f19;',
            '[data-theme="dark"] {\n      --bg: #0b0f19;\n      --primary-light: rgba(99, 102, 241, 0.18);'
        )

    # 3. Insert CSS for Plan Pill and Modals
    css_patch = """
    /* 复习计划与每日目标顶部胶囊 */
    .plan-header-container {
      display: flex;
      justify-content: center;
      padding: 6px 16px 2px 16px;
      cursor: pointer;
    }
    .plan-header-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      padding: 5px 14px;
      border-radius: 20px;
      font-size: 12.5px;
      font-weight: 600;
      color: var(--text-muted);
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      transition: all 0.2s;
    }
    .plan-header-pill:hover {
      border-color: var(--primary);
      color: var(--primary);
      transform: translateY(-1px);
    }
    .plan-card {
      border: 1.5px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      background: var(--card-bg);
      cursor: pointer;
      transition: all 0.15s ease;
      text-align: left;
    }
    .plan-card.active {
      border-color: var(--primary);
      background: var(--primary-light);
    }
    .plan-card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-weight: 700;
      font-size: 14.5px;
      color: var(--text-main);
    }
    .plan-card-badge {
      font-size: 11px;
      padding: 2px 7px;
      border-radius: 10px;
      background: var(--primary);
      color: #fff;
      font-weight: 600;
    }
    .plan-card-desc {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 4px;
      line-height: 1.4;
    }
    .plan-card-etd {
      font-size: 11.5px;
      color: var(--primary);
      font-weight: 600;
      margin-top: 5px;
      display: flex;
      align-items: center;
      gap: 4px;
    }
    .modal-btn-group {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 20px;
      width: 100%;
    }
    .modal-btn-secondary {
      width: 100%;
      height: 46px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: var(--card-bg);
      color: var(--text-main);
      font-size: 14.5px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s;
    }
    .modal-btn-secondary:active {
      background: var(--border);
    }
"""
    if '.plan-header-pill' not in html:
        html = html.replace('  </style>', css_patch + '  </style>')

    # 4. Insert Plan Header Pill below </header> if not present
    header_pill_html = """  <!-- 每日定量计划与进度状态条 -->
  <div class="plan-header-container" onclick="openPlanModal()" title="点击切换复习计划">
    <div class="plan-header-pill" id="headerPlanPill">🎯 今日计划: 0 / 60 词 | 🔥 连续打卡 1 天 | 预计 10月6日 全量通关</div>
  </div>
"""
    if 'id="headerPlanPill"' not in html:
        html = html.replace('  </header>\n\n  <!-- 顶部进度条 -->', '  </header>\n\n' + header_pill_html + '\n  <!-- 顶部进度条 -->')

    # 5. Insert Drawer Plan item if not present
    drawer_plan_html = """    <!-- 考研复习计划与每日目标 -->
    <div style="margin-bottom: 14px; padding-bottom: 12px; border-bottom: 1px solid var(--border);">
      <div style="font-size: 13px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px;">考研复习计划与每日目标：</div>
      <div class="drawer-item" onclick="closeDrawer(); openPlanModal();" style="padding: 6px 0;">
        <div>
          <div style="font-weight: 600; font-size: 14px;" id="drawerPlanName">⚡ 高效强化型 (60词/天)</div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;" id="drawerPlanDesc">预计 10月6日 全量通关 · 连续打卡 1 天</div>
        </div>
        <span style="color:var(--primary); font-weight:600; font-size:13px;">调整计划 ⚙️</span>
      </div>
    </div>
"""
    if 'id="drawerPlanName"' not in html:
        html = html.replace(
            '<h3 style="margin-bottom: 16px; font-size: 17px;">复习范围与数据管理</h3>',
            '<h3 style="margin-bottom: 16px; font-size: 17px;">复习范围与数据管理</h3>\n\n' + drawer_plan_html
        )

    # 6. Modals: dailyGoalModal and planModal
    modals_html = """  <!-- 每日定量目标达成庆祝弹窗 -->
  <div class="finish-modal" id="dailyGoalModal" style="display: none;">
    <div class="finish-content">
      <div class="finish-icon">🎯</div>
      <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 8px;">🎉 今日定量目标圆满达成！</h2>
      <p style="font-size: 14px; color: var(--text-muted); line-height: 1.6;" id="dailyGoalSummaryText">
        今日已攻克 60 / 60 词 · 连续打卡 1 天！<br>
        预计 10月6日 全量通关
      </p>
      <div class="modal-btn-group">
        <button class="finish-btn" id="btnGoalDone" onclick="finishTodayCheckin()" style="margin-top: 0; background: var(--success, #10b981);">
          今日圆满打卡 ☕
        </button>
        <button class="modal-btn-secondary" id="btnGoalContinue" onclick="continueStudying()">
          学有余力，继续挑战 ➔
        </button>
      </div>
    </div>
  </div>

  <!-- 多套复习计划方案选择弹窗 -->
  <div class="finish-modal" id="planModal" style="display: none;">
    <div class="finish-content" style="max-width: 440px; text-align: left;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <h2 style="font-size: 18px; font-weight: 800;">🎯 考研复习计划选择</h2>
        <button class="icon-btn" onclick="closePlanModal()" style="width:30px; height:30px; font-size:14px; border:none;">✕</button>
      </div>
      <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 14px; line-height: 1.4;">
        根据你的考研备战节奏选择定量方案，系统动态测算全量通关日期：
      </p>
      <div class="plan-options-list" id="planOptionsList" style="display: flex; flex-direction: column; gap: 10px;">
        <!-- 4 种方案动态渲染 -->
      </div>
      
      <div id="customPlanInputBox" style="display: none; margin-top: 10px; padding: 12px; background: var(--primary-light); border-radius: 12px;">
        <div style="display: flex; gap: 10px;">
          <div style="flex: 1;">
            <div style="font-size: 12px; font-weight: 600; color: var(--primary); margin-bottom: 6px;">每日定量 (词/天)：</div>
            <input type="number" id="customTargetInput" min="1" max="500" value="50" style="width: 100%; height: 38px; border-radius: 8px; border: 1px solid var(--border); padding: 0 10px; font-size: 14px; background: var(--card-bg); color: var(--text-main);" oninput="onCustomTargetChange()">
          </div>
          <div style="flex: 1;">
            <div style="font-size: 12px; font-weight: 600; color: var(--primary); margin-bottom: 6px;">或 目标截止日期：</div>
            <input type="date" id="customDeadlineInput" style="width: 100%; height: 38px; border-radius: 8px; border: 1px solid var(--border); padding: 0 10px; font-size: 13px; background: var(--card-bg); color: var(--text-main);" onchange="onCustomDeadlineChange()">
          </div>
        </div>
        <div id="customDeadlineHint" style="font-size: 11.5px; color: var(--text-muted); margin-top: 6px;">💡 可直接指定每日背词数，或选择考研倒计时截止日自动推算。</div>
      </div>

      <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid var(--border); font-size: 12px; color: var(--text-muted); display: flex; justify-content: space-between;" id="planModalFooterStats">
        <span id="planModalRemainingText">剩余待攻克：397 词</span>
        <span id="planModalFooterETD">预计 10月6日 全量通关</span>
      </div>
      <button class="finish-btn" onclick="saveSelectedPlan()" style="margin-top: 14px;">确认保存计划</button>
    </div>
  </div>

"""
    if 'id="dailyGoalModal"' not in html:
        html = html.replace('  <!-- 全部完成弹窗 -->', modals_html + '  <!-- 全部完成弹窗 -->')
    else:
        # If dailyGoalModal exists but needs customDeadlineInput updated
        if 'id="customDeadlineInput"' not in html:
            # Replace old customPlanInputBox
            old_box_pattern = r'<div id="customPlanInputBox"[\s\S]*?</div>\s*</div>'
            new_box = """<div id="customPlanInputBox" style="display: none; margin-top: 10px; padding: 12px; background: var(--primary-light); border-radius: 12px;">
        <div style="display: flex; gap: 10px;">
          <div style="flex: 1;">
            <div style="font-size: 12px; font-weight: 600; color: var(--primary); margin-bottom: 6px;">每日定量 (词/天)：</div>
            <input type="number" id="customTargetInput" min="1" max="500" value="50" style="width: 100%; height: 38px; border-radius: 8px; border: 1px solid var(--border); padding: 0 10px; font-size: 14px; background: var(--card-bg); color: var(--text-main);" oninput="onCustomTargetChange()">
          </div>
          <div style="flex: 1;">
            <div style="font-size: 12px; font-weight: 600; color: var(--primary); margin-bottom: 6px;">或 目标截止日期：</div>
            <input type="date" id="customDeadlineInput" style="width: 100%; height: 38px; border-radius: 8px; border: 1px solid var(--border); padding: 0 10px; font-size: 13px; background: var(--card-bg); color: var(--text-main);" onchange="onCustomDeadlineChange()">
          </div>
        </div>
        <div id="customDeadlineHint" style="font-size: 11.5px; color: var(--text-muted); margin-top: 6px;">💡 可直接指定每日背词数，或选择考研倒计时截止日自动推算。</div>
      </div>"""
            html = re.sub(r'<div id="customPlanInputBox"[\s\S]*?</div>\s*</div>', new_box + '\n      </div>', html, count=1)

    # 7. Replace the entire script block starting from "// 考研复习计划方案定义" or "// 应用运行状态" down to "</script>"
    script_pattern = r'(// 考研复习计划方案定义|// 应用运行状态)[\s\S]*?</script>'
    new_script = build_full_script() + '\n  </script>'
    m = re.search(script_pattern, html)
    if m:
        html = html[:m.start()] + new_script + html[m.end():]
    else:
        print("Warning: could not find script block to replace in", filepath)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Successfully patched {filepath}!")

if __name__ == '__main__':
    patch_file('index.html')
    patch_file('考研英语刷题卡.html')
