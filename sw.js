// 考研英语刷题卡 Service Worker (PWA 离线复习支持)
const CACHE_VERSION = 'v1.2.1';
const CACHE_NAME = `kaoyan-cards-pwa-${CACHE_VERSION}`;

// 核心离线预缓存资源清单
const STATIC_ASSETS = [
  './',
  './index.html',
  './考研英语刷题卡.html',
  './manifest.json',
  './cards.json',
  './version.json',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/apple-touch-icon.png',
  './favicon.svg',
  './favicon.png'
];

// 安装阶段：预缓存核心资源并快速激活
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // 使用 cache.addAll 结合宽松容错，避免单一文件缺失导致安装失败
      return Promise.allSettled(
        STATIC_ASSETS.map(url =>
          cache.add(new Request(url, { cache: 'reload' })).catch(err => {
            console.warn(`[PWA SW] Pre-caching item failed: ${url}`, err);
          })
        )
      );
    }).then(() => {
      return self.skipWaiting();
    })
  );
});

// 激活阶段：清理旧版本缓存，夺取控制权
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(name => {
          if (name !== CACHE_NAME) {
            console.log(`[PWA SW] Cleaning old cache: ${name}`);
            return caches.delete(name);
          }
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// 消息监听：支持强制立即刷新
self.addEventListener('message', event => {
  if (event.data && event.data.action === 'skipWaiting') {
    self.skipWaiting();
  }
});

// 请求拦截策略
self.addEventListener('fetch', event => {
  const request = event.request;
  const url = new URL(request.url);

  // 只处理 GET 请求及本域同源协议
  if (request.method !== 'GET') return;
  if (!url.protocol.startsWith('http')) return;

  // 1. version.json 与 cards.json：网络优先 (Network-First)，确保在线时能检测到 OTA 热更新
  if (url.pathname.endsWith('version.json') || url.pathname.endsWith('cards.json')) {
    event.respondWith(
      fetch(request).then(response => {
        if (response && response.status === 200) {
          const respClone = response.clone();
          caches.open(CACHE_NAME).then(cache => {
            // 同时缓存原始请求与规范化纯净路径，彻底避免时间戳 ?_t= 导致离线未命中
            cache.put(request, respClone.clone());
            cache.put(url.pathname, respClone);
          });
        }
        return response;
      }).catch(async () => {
        // 网络失败或离线时，回退至本地缓存 (显式 ignoreSearch 忽略防缓存时间戳)
        const cached = await caches.match(request, { ignoreSearch: true }) || await caches.match(url.pathname);
        if (cached) return cached;
        return new Response(JSON.stringify({ offline: true }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // 2. 静态页面与资源：Stale-While-Revalidate 策略
  // 离线秒开，后台自动更新，自习室/地铁无网环境稳定使用
  event.respondWith(
    caches.match(request, { ignoreSearch: true }).then(async cachedResponse => {
      const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse && networkResponse.status === 200) {
          const respClone = networkResponse.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, respClone));
        }
        return networkResponse;
      }).catch(err => {
        // 离线网络错误静默处理
        return cachedResponse;
      });

      if (cachedResponse) {
        return cachedResponse;
      }

      // 如果缓存未直接命中，等待网络响应；若网络失败且属于单页导航请求，回退至 index.html
      try {
        const netResp = await fetchPromise;
        if (netResp) return netResp;
      } catch (e) {}

      if (request.mode === 'navigate') {
        const fallback = await caches.match('./index.html') || await caches.match('./');
        if (fallback) return fallback;
      }

      return new Response('Offline', { status: 503, statusText: 'Offline' });
    })
  );
});
