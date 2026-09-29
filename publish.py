# -*- coding: utf-8 -*-
"""
考研英语真题精读刷题卡 - 一键云端发布与 OTA 部署脚本
功能：
  1. 自动扫描并聚合所有 data_20xx.py 题库数据
  2. 生成并更新 cards.json 全量题库
  3. 自动递增或更新 version.json 版本元数据与时间戳
  4. 同步更新 sw.js (Service Worker) 缓存版本号
  5. 同步内嵌题库至 考研英语刷题卡.html 与 index.html (供 GitHub Pages / Vercel 根目录直连)
  6. 自动执行全套自动化回归测试 (test_app, test_cloze_and_notes, test_pwa_and_ota)
  7. 自动执行 Git 本地工作流 (git init / git add / git commit / git push)
"""

import os
import sys
import glob
import json
import re
import datetime
import subprocess
import importlib

# 强制 UTF-8 控制台输出
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def log(msg):
    print(f"[Publish] {msg}")

def run_cmd(cmd_list, check=True, timeout=20):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        res = subprocess.run(cmd_list, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout, env=env)
        if check and res.returncode != 0:
            log(f"Command failed ({' '.join(cmd_list)}):\n{res.stderr.strip()}")
        return res
    except subprocess.TimeoutExpired:
        log(f"Command timed out ({' '.join(cmd_list)})")
        class FakeRes:
            returncode = 1
            stdout = ""
            stderr = "Command timed out"
        return FakeRes()

def get_all_cards():
    """动态扫描并加载所有 data_20xx.py 中的卡片"""
    data_files = sorted(glob.glob("data_20*.py"))
    log(f"发现数据模块: {data_files}")
    
    total_cards = []
    for df in data_files:
        mod_name = os.path.splitext(os.path.basename(df))[0]
        if mod_name in sys.modules:
            mod = importlib.reload(sys.modules[mod_name])
        else:
            mod = importlib.import_module(mod_name)
        
        # 提取模块中所有 cards_* 列表
        for attr in sorted(dir(mod)):
            if attr.startswith("cards_"):
                val = getattr(mod, attr)
                if isinstance(val, list):
                    total_cards.extend(val)
                    
    log(f"已聚合总卡片数: {len(total_cards)} 张")
    return total_cards

def bump_version(ver_str):
    parts = ver_str.strip().split('.')
    try:
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)
    except Exception:
        return ver_str + ".1"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="考研英语刷题卡一键发布工具")
    parser.add_argument("--version", dest="set_version", help="指定发布的版本号，如 1.0.1")
    parser.add_argument("--bump", action="store_true", help="自动递增版本号末位")
    parser.add_argument("--msg", dest="commit_msg", help="自定义 Git 提交说明")
    parser.add_argument("--no-git", action="store_true", help="跳过 Git 操作")
    args = parser.parse_args()

    print("=" * 60)
    log("🚀 开始执行考研英语刷题卡构建与发布流程...")
    print("=" * 60)

    # 1. 聚合卡片数据
    all_cards = get_all_cards()
    assert len(all_cards) > 0, "未找到任何卡片数据！"

    # 2. 读取并更新 version.json
    ver_file = "version.json"
    current_ver = "1.0.0"
    if os.path.exists(ver_file):
        try:
            with open(ver_file, 'r', encoding='utf-8') as f:
                old_info = json.load(f)
                current_ver = old_info.get("version", "1.0.0")
        except Exception as e:
            log(f"读取旧版 version.json 提示: {e}")

    if args.set_version:
        new_ver = args.set_version
    elif args.bump:
        new_ver = bump_version(current_ver)
    else:
        new_ver = current_ver

    years = sorted(list(set(c['year'] for c in all_cards)))
    latest_year = max(years) if years else 2010
    latest_texts = [c['text'] for c in all_cards if c['year'] == latest_year]
    latest_text = latest_texts[-1] if latest_texts else "Text 1"

    now_iso = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    version_info = {
        "version": new_ver,
        "updatedAt": now_iso,
        "totalCards": len(all_cards),
        "years": years,
        "latestYear": latest_year,
        "latestText": latest_text,
        "releaseNotes": f"{min(years)}-{latest_year}年真题精读考点全覆盖 (共{len(all_cards)}词)"
    }

    with open(ver_file, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, ensure_ascii=False, indent=2)
    log(f"✓ 已生成最新 {ver_file} (版本: v{new_ver}, 总词数: {len(all_cards)})")

    # 3. 输出 cards.json
    with open("cards.json", 'w', encoding='utf-8') as f:
        json.dump(all_cards, f, ensure_ascii=False, indent=2)
    log(f"✓ 已更新 cards.json (共 {len(all_cards)} 张卡片)")

    # 4. 更新 sw.js 缓存版本号
    if os.path.exists("sw.js"):
        with open("sw.js", 'r', encoding='utf-8') as f:
            sw_code = f.read()
        sw_code = re.sub(r"const CACHE_VERSION = '.*?';", f"const CACHE_VERSION = 'v{new_ver}';", sw_code)
        with open("sw.js", 'w', encoding='utf-8') as f:
            f.write(sw_code)
        log(f"✓ 已将 sw.js Service Worker 缓存版本更新为: v{new_ver}")

    # 5. 更新 考研英语刷题卡.html 中的内嵌 ALL_CARDS 与 APP_VERSION
    html_target = "考研英语刷题卡.html"
    if os.path.exists(html_target):
        with open(html_target, 'r', encoding='utf-8') as f:
            html = f.read()
        
        cards_js_str = "    const ALL_CARDS = " + json.dumps(all_cards, ensure_ascii=False, indent=6) + ";"
        pattern = r'const ALL_CARDS = \[.*?\];'
        if re.search(pattern, html, re.DOTALL):
            html = re.sub(pattern, cards_js_str, html, flags=re.DOTALL)

        # 同步内置 APP_VERSION 常量
        html = re.sub(r"const APP_VERSION = '.*?';", f"const APP_VERSION = '{new_ver}';", html)

        # 同步底部版本说明
        html = re.sub(
            r'id="appVersionInfo">\s*题库版本：.*?· 支持离线PWA',
            f'id="appVersionInfo">\n      题库版本：v{new_ver} ({len(all_cards)}词) · 支持离线PWA',
            html
        )
        
        with open(html_target, 'w', encoding='utf-8') as f:
            f.write(html)
        log(f"✓ 已同步最新题库与版本号 v{new_ver} 到 {html_target}")

        # 6. 同步写入 index.html (根目录直连入口)
        with open("index.html", 'w', encoding='utf-8') as f:
            f.write(html)
        log("✓ 已将最新代码完整同步至 index.html (供 GitHub Pages / Vercel 直连)")

    # 7. 运行全套自动化测试
    log("🧪 正在运行自动化测试验证套件...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    r1 = subprocess.run([sys.executable, "test_app.py"], env=env, capture_output=True, text=True, encoding='utf-8')
    assert r1.returncode == 0, f"test_app.py 失败:\n{r1.stdout}\n{r1.stderr}"
    log("✓ test_app.py 通过")

    r2 = subprocess.run([sys.executable, "test_cloze_and_notes.py"], env=env, capture_output=True, text=True, encoding='utf-8')
    assert r2.returncode == 0, f"test_cloze_and_notes.py 失败:\n{r2.stdout}\n{r2.stderr}"
    log("✓ test_cloze_and_notes.py 通过")

    r3 = subprocess.run([sys.executable, "test_pwa_and_ota.py"], env=env, capture_output=True, text=True, encoding='utf-8')
    assert r3.returncode == 0, f"test_pwa_and_ota.py 失败:\n{r3.stdout}\n{r3.stderr}"
    log("✓ test_pwa_and_ota.py (PWA & OTA 专项测试) 通过")

    import shutil
    if shutil.which("node") and os.path.exists("test_edge_cases.js"):
        r4 = subprocess.run(["node", "test_edge_cases.js"], capture_output=True, text=True, encoding='utf-8')
        assert r4.returncode == 0, f"test_edge_cases.js 失败:\n{r4.stdout}\n{r4.stderr}"
        log("✓ test_edge_cases.js (深度边缘用例与攻击仿真测试) 通过")

    if shutil.which("node") and os.path.exists("test_comprehensive_features.js"):
        r5 = subprocess.run(["node", "test_comprehensive_features.js"], capture_output=True, text=True, encoding='utf-8')
        assert r5.returncode == 0, f"test_comprehensive_features.js 失败:\n{r5.stdout}\n{r5.stderr}"
        log("✓ test_comprehensive_features.js (核心释义/考点讲解双板块与原句翻译测试) 通过")

    if shutil.which("node") and os.path.exists("test_plan_and_quota.js"):
        r6 = subprocess.run(["node", "test_plan_and_quota.js"], capture_output=True, text=True, encoding='utf-8')
        assert r6.returncode == 0, f"test_plan_and_quota.js 失败:\n{r6.stdout}\n{r6.stderr}"
        log("✓ test_plan_and_quota.js (多套复习计划、每日定量推送与断点续学测试) 通过")

    # 8. Git 本地与云端同步
    if not args.no_git:
        log("📦 检查 Git 版本控制状态...")
        has_git_dir = os.path.exists(".git")
        if not has_git_dir:
            log("初始化 Git 仓库 (git init)...")
            run_cmd(["git", "init", "-b", "main"])
        
        # 添加全部变动文件
        run_cmd(["git", "add", "-A"])
        
        commit_message = args.commit_msg or f"🚀 发布题库 v{new_ver}: 包含 {min(years)}-{latest_year} 年真题精读 (共 {len(all_cards)} 词)"
        c_res = run_cmd(["git", "commit", "-m", commit_message], check=False)
        if c_res.returncode == 0:
            log(f"✓ Git 提交成功: {commit_message}")
        else:
            if "nothing to commit" in c_res.stdout or "nothing to commit" in c_res.stderr:
                log("Git 工作区干净，无新增文件需要提交。")
            else:
                log(f"Git commit 输出: {c_res.stdout or c_res.stderr}")

        # 检查 remote
        rem_res = run_cmd(["git", "remote", "-v"], check=False)
        if "origin" in rem_res.stdout:
            log("正在推送到 GitHub 远程仓库 (git push)...")
            try:
                # 允许 Git Credential Manager 在控制台/浏览器中完成首次交互登录
                p_code = subprocess.run(["git", "push", "-u", "origin", "main"]).returncode
                if p_code == 0:
                    log("🎉 已成功推送到 GitHub 远程仓库！")
                else:
                    log("⚠️ 命令行推送未完成。如果你尚未在终端登录 GitHub，可以直接在网页端上传：")
                    log("   打开 GitHub 仓库页面 -> 点击【Add file】->【Upload files】")
                    log("   拖入 index.html, cards.json, version.json 点击 Commit changes 即可！")
            except Exception as e:
                log(f"推送异常: {e}")
        else:
            log("💡 提示：当前尚未绑定 GitHub 远程仓库。")
            log("如需绑定并开启 GitHub Pages 免费云托管，只需执行：")
            log("  1) 在 GitHub 上新建仓库 (如 kaoyan-cards)")
            log("  2) git remote add origin https://github.com/<你的用户名>/kaoyan-cards.git")
            log("  3) git push -u origin main")

    print("=" * 60)
    log(f"🎉 全部发布与构建流程顺利完成！当前卡片总数: {len(all_cards)}, 题库版本: v{new_ver}")
    print("=" * 60)

if __name__ == "__main__":
    main()
