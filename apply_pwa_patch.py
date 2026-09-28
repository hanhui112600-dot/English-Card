# -*- coding: utf-8 -*-
import re
import json

with open('考研英语刷题卡.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. 注入 Head PWA 标签
pwa_meta_tags = """  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="考研刷题卡">
  <meta name="theme-color" content="#4f46e5">
  <meta name="description" content="考研英语历年真题精读知识点闪卡系统，支持离线PWA与云端OTA热更新">
  <link rel="manifest" href="manifest.json">
  <link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
  <link rel="icon" type="image/svg+xml" href="icons/icon.svg">
  <link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
  <link rel="icon" type="image/png" sizes="512x512" href="icons/icon-512.png">
  <link rel="shortcut icon" href="favicon.png">"""

if '<link rel="manifest"' not in html:
    old_head_meta = """  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="考研刷题卡">
  <meta name="theme-color" content="#4f46e5">"""
    if old_head_meta in html:
        html = html.replace(old_head_meta, pwa_meta_tags)
        print("✓ Injected PWA head meta and link tags")
    else:
        print("! Could not find exact old_head_meta")

# 2. 注入 Toast 样式
toast_css = """    /* 顶部浮动提示条 (OTA 同步 / 离线提醒 / 快捷提示) */
    .toast-notification {
      position: fixed;
      top: calc(env(safe-area-inset-top, 16px) + 12px);
      left: 50%;
      transform: translateX(-50%) translateY(-100px);
      background: rgba(19, 27, 46, 0.95);
      color: #f8fafc;
      padding: 10px 20px;
      border-radius: 30px;
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.15);
      z-index: 10000;
      transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.35s ease;
      opacity: 0;
      pointer-events: none;
      max-width: 90vw;
      text-align: center;
      backdrop-filter: blur(10px);
      -webkit-backdrop-filter: blur(10px);
    }
    .toast-notification.show {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
      pointer-events: auto;
    }
    [data-theme="light"] .toast-notification {
      background: rgba(15, 23, 42, 0.92);
      color: #ffffff;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(0, 0, 0, 0.08);
    }
"""

if '.toast-notification' not in html:
    html = html.replace('  </style>', toast_css + '  </style>')
    print("✓ Injected Toast notification CSS styles")

# 3. 注入 Toast DOM 元素
if 'id="toastNotification"' not in html:
    html = html.replace('<body>', '<body>\n  <div class="toast-notification" id="toastNotification"></div>')
    print("✓ Injected Toast notification DOM element")

# 4. 注入抽屉内的“联网检查更新”及版本信息
old_drawer_guide = """    <div class="drawer-item" onclick="alert('提示：在手机 Safari 或 Chrome 浏览器中，点击【分享】或【设置】，选择【添加到主屏幕】，即可像真正的 App 一样离线全屏使用！')">
      <span>📱 如何在手机上当独立 App 用？</span>
      <span style="color:var(--primary); font-size:13px;">查看指南</span>
    </div>"""

new_drawer_items = """    <div class="drawer-item" onclick="checkOTAUpdate(false)">
      <span>🔄 联网检查更新</span>
      <span style="color:var(--primary); font-size:13px;" id="drawerVersionBadge">检查最新</span>
    </div>

    <div class="drawer-item" onclick="showPwaGuide()">
      <span>📱 如何在手机上当独立 App 用？</span>
      <span style="color:var(--primary); font-size:13px;">查看指南</span>
    </div>

    <div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); text-align: center; font-size: 11px; color: var(--text-muted);" id="appVersionInfo">
      题库版本：v1.0.0 (397词) · 支持离线PWA
    </div>"""

if 'checkOTAUpdate(false)' not in html:
    if old_drawer_guide in html:
        html = html.replace(old_drawer_guide, new_drawer_items)
        print("✓ Updated drawer items with OTA check and version info")
    else:
        print("! Could not find old_drawer_guide")

# 5. 注入 OTA 脚本与 Service Worker 逻辑
ota_js_functions = """
    // 本地 OTA 离线热更新优先加载策略
    (function initOTACards() {
      try {
        const cached = localStorage.getItem('kaoyan_ota_cards');
        if (cached) {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length >= ALL_CARDS.length) {
            ALL_CARDS.length = 0;
            ALL_CARDS.push(...parsed);
          }
        }
      } catch (e) {
        console.warn('Init OTA cards error:', e);
      }
    })();

    // 轻量浮动提示条
    function showToast(msg, duration = 3000) {
      let toast = document.getElementById('toastNotification');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toastNotification';
        toast.className = 'toast-notification';
        document.body.appendChild(toast);
      }
      toast.innerHTML = msg;
      toast.classList.add('show');
      clearTimeout(window._toastTimeout);
      window._toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
      }, duration);
    }

    // PWA 添加主屏幕指南
    function showPwaGuide() {
      const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
      if (isIOS) {
        alert("【苹果 iOS (Safari) 添加指南】\\n1. 点击 Safari 底部中间的「分享」按钮 (箭头向上图标)\\n2. 向上滑动菜单，点击「添加到主屏幕」\\n3. 点击右上角「添加」，即可像原生 App 一样全屏离线使用！");
      } else {
        alert("【安卓 Android (Chrome / Edge) 添加指南】\\n1. 点击浏览器右上角「三个点」菜单\\n2. 选择「安装应用」或「添加到主屏幕」\\n3. 确认后手机桌面即生成专属应用图标，支持完全离线刷题！");
      }
    }

    // 严谨应用新题库 (核心红线：严禁清空或覆盖用户的掌握与错题进度)
    function applyNewCards(newCards, version, isSilent) {
      if (!Array.isArray(newCards) || newCards.length === 0) return;
      
      // 更新内存中的卡片库
      ALL_CARDS.length = 0;
      ALL_CARDS.push(...newCards);
      
      try {
        localStorage.setItem('kaoyan_ota_cards', JSON.stringify(newCards));
        if (version) localStorage.setItem('kaoyan_cards_version', version);
      } catch (e) {
        console.warn('Storage quota or error saving OTA cards:', e);
      }
      
      renderYearBar();
      renderScopeBar();
      renderCategoryChips();
      buildQueue();
      
      const verText = version ? `v${version}` : '';
      const msg = `🎉 发现新卡片库已同步！${verText} (共 ${ALL_CARDS.length} 词)`;
      showToast(msg, 3500);
      
      const badge = document.getElementById('drawerVersionBadge');
      if (badge) badge.textContent = verText || '已是最新';
      const verInfo = document.getElementById('appVersionInfo');
      if (verInfo) verInfo.textContent = `题库版本：${verText || '最新'} (${ALL_CARDS.length}词) · 支持离线PWA`;
    }

    // 联网检查更新 (OTA 热更新)
    async function checkOTAUpdate(silent = true) {
      if (!silent) {
        showToast('🔄 正在联网检查最新题库...', 2000);
      }
      try {
        const verRes = await fetch('./version.json?_t=' + Date.now(), { cache: 'no-store' });
        if (!verRes.ok) throw new Error(`HTTP ${verRes.status}`);
        const verData = await verRes.json();
        const localVer = localStorage.getItem('kaoyan_cards_version') || '1.0.0';
        const currentCount = ALL_CARDS.length;

        // 如果线上版本更高，或题目总数不一致
        if (verData.version !== localVer || (verData.totalCards && verData.totalCards !== currentCount)) {
          const cardsRes = await fetch('./cards.json?_t=' + Date.now(), { cache: 'no-store' });
          if (!cardsRes.ok) throw new Error(`HTTP ${cardsRes.status} fetching cards`);
          const newCards = await cardsRes.json();
          applyNewCards(newCards, verData.version, silent);
          return;
        }

        const badge = document.getElementById('drawerVersionBadge');
        if (badge) badge.textContent = `v${verData.version || localVer}`;
        const verInfo = document.getElementById('appVersionInfo');
        if (verInfo) verInfo.textContent = `题库版本：v${verData.version || localVer} (${currentCount}词) · 支持离线PWA`;

        if (!silent) {
          showToast(`✅ 当前已是最新卡片库 (v${verData.version || localVer}，共 ${currentCount} 词)`, 2500);
        }
      } catch (err) {
        console.warn('[OTA] Check failed:', err);
        if (!silent) {
          showToast(`📶 当前处于离线状态，离线题库正常可用 (共 ${ALL_CARDS.length} 词)`, 3000);
        }
      }
    }

    // 注册 PWA Service Worker
    function registerPWA() {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js').then(reg => {
          console.log('[PWA] Service Worker registered:', reg.scope);
          reg.onupdatefound = () => {
            const installingWorker = reg.installing;
            if (installingWorker) {
              installingWorker.onstatechange = () => {
                if (installingWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  showToast('✨ 刷题卡新核心已就绪，下次打开将自动应用');
                }
              };
            }
          };
        }).catch(err => {
          console.warn('[PWA] Service Worker registration failed:', err);
        });
      }
    }
"""

if 'function checkOTAUpdate' not in html:
    # 插入在 ALL_CARDS 后面、let state 之前
    pattern_state = '    // 应用运行状态\n    let state = {'
    if pattern_state in html:
        html = html.replace(pattern_state, ota_js_functions + '\n' + pattern_state)
        print("✓ Injected OTA and PWA JS functions")
    else:
        print("! Could not find pattern_state")

# 6. 更新 window.onload 初始化逻辑
old_onload = """    // 初始化
    window.onload = () => {
      const savedTheme = localStorage.getItem('kaoyan_theme');
      if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);
      loadSavedState();
      renderYearBar();
      renderScopeBar();
      buildQueue();
    };"""

new_onload = """    // 初始化
    window.onload = () => {
      const savedTheme = localStorage.getItem('kaoyan_theme');
      if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);
      loadSavedState();
      renderYearBar();
      renderScopeBar();
      buildQueue();
      registerPWA();

      // 在线时安静执行 OTA 检查
      if (navigator.onLine) {
        setTimeout(() => { checkOTAUpdate(true); }, 1500);
      }
      window.addEventListener('online', () => {
        showToast('🌐 网络已恢复，正在同步最新题库...', 2000);
        checkOTAUpdate(true);
      });
    };"""

if old_onload in html:
    html = html.replace(old_onload, new_onload)
    print("✓ Updated window.onload with registerPWA and auto OTA check")
else:
    print("! Could not find old_onload")

# 写回 考研英语刷题卡.html
with open('考研英语刷题卡.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Updated 考研英语刷题卡.html")

# 同时同步写入 index.html
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("Synchronized to index.html successfully!")
