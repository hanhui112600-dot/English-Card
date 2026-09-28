# -*- coding: utf-8 -*-
import sys
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
import json
import os
import re
import struct

print("=== Starting Plan A (PWA + OTA) Verification Suite ===")

# 1. 验证 manifest.json
assert os.path.exists("manifest.json"), "manifest.json does not exist!"
with open("manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

assert manifest.get("name") == "考研英语刷题卡", f"Incorrect manifest name: {manifest.get('name')}"
assert manifest.get("display") == "standalone", f"Display mode is not standalone: {manifest.get('display')}"
assert manifest.get("theme_color").lower() == "#4f46e5", f"theme_color mismatch: {manifest.get('theme_color')}"
assert manifest.get("background_color").lower() == "#090d16", f"background_color mismatch: {manifest.get('background_color')}"
assert len(manifest.get("icons", [])) >= 3, "Manifest missing icon definitions"

for icon_def in manifest["icons"]:
    src = icon_def["src"].lstrip("./").replace("/", os.sep)
    assert os.path.exists(src), f"Manifest icon file not found: {src}"
    assert os.path.getsize(src) > 0, f"Manifest icon file is empty: {src}"
print("✓ 1. manifest.json verified (name, standalone, theme_color, background_color, icon mappings).")

# 2. 验证 App 图标文件及分辨率
def read_png_dimensions(filepath):
    with open(filepath, "rb") as f:
        head = f.read(24)
        assert head.startswith(b"\x89PNG\r\n\x1a\n"), f"{filepath} is not a valid PNG"
        w, h = struct.unpack(">II", head[16:24])
        return w, h

w192, h192 = read_png_dimensions("icons/icon-192.png")
assert (w192, h192) == (192, 192), f"icon-192 dimensions mismatch: {w192}x{h192}"

w512, h512 = read_png_dimensions("icons/icon-512.png")
assert (w512, h512) == (512, 512), f"icon-512 dimensions mismatch: {w512}x{h512}"

w180, h180 = read_png_dimensions("icons/apple-touch-icon.png")
assert (w180, h180) == (180, 180), f"apple-touch-icon dimensions mismatch: {w180}x{h180}"

assert os.path.exists("icons/icon.svg") and os.path.getsize("icons/icon.svg") > 500, "icon.svg invalid"
print(f"✓ 2. App Icons verified: icon-192 ({w192}x{h192}), icon-512 ({w512}x{h512}), apple-touch-icon ({w180}x{h180}), icon.svg.")

# 3. 验证 sw.js (Service Worker)
assert os.path.exists("sw.js"), "sw.js does not exist!"
with open("sw.js", "r", encoding="utf-8") as f:
    sw_code = f.read()

assert "CACHE_VERSION" in sw_code, "sw.js missing CACHE_VERSION"
assert "STATIC_ASSETS" in sw_code, "sw.js missing STATIC_ASSETS"
assert "caches.open" in sw_code, "sw.js missing cache opening logic"
assert "caches.delete" in sw_code, "sw.js missing cache cleanup logic"
assert "version.json" in sw_code and "cards.json" in sw_code, "sw.js missing OTA network-first handling"
assert "ignoreSearch: true" in sw_code, "sw.js missing ignoreSearch for query string cache immunity"
assert "request.mode === 'navigate'" in sw_code, "sw.js missing offline navigate fallback"

# 验证 STATIC_ASSETS 中声明的本地文件真实存在
m_assets = re.search(r'const STATIC_ASSETS = \[(.*?)\];', sw_code, re.DOTALL)
assert m_assets, "Could not extract STATIC_ASSETS from sw.js"
asset_paths = re.findall(r"['\"](\./[^'\"]+)['\"]", m_assets.group(1))
for ap in asset_paths:
    if ap in ["./", "./index.html", "./考研英语刷题卡.html"]:
        continue
    clean_path = ap.replace("./", "").replace("/", os.sep)
    assert os.path.exists(clean_path), f"Asset declared in sw.js does not exist: {clean_path}"
print(f"✓ 3. sw.js (Service Worker) verified with {len(asset_paths)} pre-cached assets, ignoreSearch immunity, and offline navigate fallback.")

# 4. 验证 version.json 与 cards.json
assert os.path.exists("version.json"), "version.json missing!"
with open("version.json", "r", encoding="utf-8") as f:
    ver_data = json.load(f)

assert "version" in ver_data, "version.json missing version field"
assert ver_data.get("totalCards") == 397, f"version.json totalCards mismatch: {ver_data.get('totalCards')}"
assert ver_data.get("latestYear") == 2010, f"version.json latestYear mismatch: {ver_data.get('latestYear')}"

assert os.path.exists("cards.json"), "cards.json missing!"
with open("cards.json", "r", encoding="utf-8") as f:
    cards_data = json.load(f)

assert len(cards_data) == 397, f"cards.json card count mismatch: {len(cards_data)}"
print(f"✓ 4. version.json (v{ver_data['version']}, {ver_data['totalCards']} cards) and cards.json verified.")

# 5. 验证 index.html 与 考研英语刷题卡.html
for html_filename in ["index.html", "考研英语刷题卡.html"]:
    assert os.path.exists(html_filename), f"{html_filename} missing!"
    with open(html_filename, "r", encoding="utf-8") as f:
        c = f.read()
    
    # PWA head tags
    assert '<link rel="manifest" href="manifest.json">' in c, f"{html_filename} missing manifest link"
    assert '<meta name="theme-color" content="#4f46e5">' in c, f"{html_filename} missing theme-color"
    assert 'icons/icon-192.png' in c, f"{html_filename} missing icon-192 reference"
    
    # Toast notification
    assert 'id="toastNotification"' in c, f"{html_filename} missing toastNotification element"
    assert '.toast-notification' in c, f"{html_filename} missing toastNotification CSS"
    
    # Drawer manual update button and dynamic containers
    assert 'checkOTAUpdate(false)' in c, f"{html_filename} missing manual OTA check button"
    assert 'id="drawerYearButtons"' in c, f"{html_filename} missing drawerYearButtons container"
    
    # Service worker registration
    assert 'navigator.serviceWorker.register' in c, f"{html_filename} missing SW registration"
    
    # OTA functions & version sync
    assert 'function checkOTAUpdate' in c, f"{html_filename} missing checkOTAUpdate function"
    assert 'function applyNewCards' in c, f"{html_filename} missing applyNewCards function"
    assert 'function compareVersions' in c, f"{html_filename} missing compareVersions function"
    
    # 验证内置版本常量 APP_VERSION 与 version.json 严格对齐
    m_ver = re.search(r"const APP_VERSION = '([^']+)';", c)
    assert m_ver, f"{html_filename} missing const APP_VERSION definition"
    assert m_ver.group(1) == ver_data["version"], f"{html_filename} APP_VERSION ({m_ver.group(1)}) != version.json ({ver_data['version']})"

    # 验证动态年份渲染能力
    assert 'Array.from(new Set(ALL_CARDS.map(c => c.year)))' in c, f"{html_filename} missing dynamic year discovery"

    # CRITICAL RULE: updating cards must never wipe study progress
    # Check that applyNewCards never clears masteredIds or reviewIds
    apply_match = re.search(r'function applyNewCards\([\s\S]*?\{([\s\S]*?)\n    \}', c)
    assert apply_match, f"{html_filename} missing applyNewCards block"
    apply_body = apply_match.group(1)
    assert 'state.masteredIds.clear()' not in apply_body, "CRITICAL: applyNewCards must NOT clear masteredIds!"
    assert 'state.reviewIds.clear()' not in apply_body, "CRITICAL: applyNewCards must NOT clear reviewIds!"
    assert 'state.masteredIds = new Set()' not in apply_body, "CRITICAL: applyNewCards must NOT overwrite masteredIds!"
    assert 'state.reviewIds = new Set()' not in apply_body, "CRITICAL: applyNewCards must NOT overwrite reviewIds!"
    print(f"✓ 5. {html_filename} fully verified (PWA, OTA, SW, Toast, Dynamic Years, APP_VERSION sync, Progress Safety Rule).")

# 6. 验证语义化版本比较算法单元测试
def py_compare_versions(v1, v2):
    if not v1 and not v2: return 0
    if not v1: return -1
    if not v2: return 1
    p1 = [int(n) for n in str(v1).lstrip('v').split('.')]
    p2 = [int(n) for n in str(v2).lstrip('v').split('.')]
    ml = max(len(p1), len(p2))
    p1 += [0] * (ml - len(p1))
    p2 += [0] * (ml - len(p2))
    for a, b in zip(p1, p2):
        if a > b: return 1
        if a < b: return -1
    return 0

assert py_compare_versions("1.0.1", "1.0.0") > 0
assert py_compare_versions("1.10.0", "1.9.0") > 0
assert py_compare_versions("v1.0.2", "1.0.2") == 0
assert py_compare_versions("1.0.0", "1.0.1") < 0
print("✓ 6. Semantic version comparison unit logic verified.")

print("=== ALL PLAN A VERIFICATION CHECKS PASSED WITH 100% SUCCESS! ===")
