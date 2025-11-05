# src/main.py (最终修复版: 自动补全 domain/path 并修正 sameSite)
import os
import sys
import json
import requests
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

CONFIG_FILE = '/data/config.json'

TELEGRAM_BOT_TOKEN = None
TELEGRAM_CHAT_ID = None

def load_config():
    """从 JSON 文件加载配置"""
    global TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        TELEGRAM_BOT_TOKEN = config.get('global', {}).get('TELEGRAM_BOT_TOKEN')
        TELEGRAM_CHAT_ID = config.get('global', {}).get('TELEGRAM_CHAT_ID')
        return config
    except FileNotFoundError:
        print(f"错误: 配置文件 {CONFIG_FILE} 未找到。")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"错误: 配置文件 {CONFIG_FILE} 格式无效。")
        sys.exit(1)

def send_telegram_notification(html_message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("警告：未配置 Telegram 的 BOT_TOKEN 或 CHAT_ID，跳过发送通知。")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': html_message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"发送 Telegram 通知失败：{response.text}")
    except Exception as e:
        print(f"发送 Telegram 通知时发生网络错误：{e}")


def login_to_site(site_config):
    auth_method = site_config.get('AUTH_METHOD', 'form').lower()
    cookie_json_str = site_config.get('COOKIE')
    url = site_config.get('URL')
    verify_selector = site_config.get('VERIFY_SELECTOR')

    print(f"开始尝试登录: {url} (模式: {auth_method})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.g Roaming/Mozilla/Firefox/Profiles/44fvp041.default-release/cookies.sqlite0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            if auth_method == 'cookie':
                if not cookie_json_str or not verify_selector:
                    return False, "Cookie 模式需要 <code>COOKIE</code> 和 <code>VERIFY_SELECTOR</code>。"
                
                try:
                    cookies = json.loads(cookie_json_str)
                    if isinstance(cookies, dict):
                        cookies = [cookies]
                except json.JSONDecodeError:
                    return False, "<b>失败步骤:</b> 解析 Cookie\n<b>错误:</b> Cookie 格式无效，请输入一个有效的 JSON 数组或对象。"
                
                # --- (终极修复：自动补全和修正 Cookie) ---
                print("正在处理和净化 Cookie...")
                parsed_url = urlparse(url)
                base_domain = parsed_url.netloc
                if base_domain.startswith('www.'):
                    base_domain = base_domain[4:]
                
                final_cookies = []
                for cookie in cookies:
                    # 1. 自动补全 domain 和 path (如果缺失)
                    if 'domain' not in cookie or not cookie['domain']:
                        cookie['domain'] = f".{base_domain}"
                        print(f"  > 为 Cookie '{cookie['name']}' 自动补全 domain: {cookie['domain']}")
                    if 'path' not in cookie or not cookie['path']:
                        cookie['path'] = '/'
                        print(f"  > 为 Cookie '{cookie['name']}' 自动补全 path: {cookie['path']}")

                    # 2. 自动修正 sameSite 大小写
                    if 'sameSite' in cookie and isinstance(cookie['sameSite'], str):
                        capitalized_same_site = cookie['sameSite'].capitalize()
                        if capitalized_same_site in ['Lax', 'Strict', 'None']:
                            cookie['sameSite'] = capitalized_same_site
                        else:
                            del cookie['sameSite'] # 移除无法识别的值
                    
                    final_cookies.append(cookie)
                # --- (修复结束) ---

                context.add_cookies(final_cookies) # 使用最完美的 Cookie 列表
                page = context.new_page()
                page.goto(url, timeout=30000)
                print("JSON Cookie 已注入，正在验证登录状态...")
                try:
                    page.locator(verify_selector).wait_for(timeout=15000)
                    print("   验证成功！")
                    return True, "使用 JSON Cookie 成功认证。"
                except PlaywrightTimeoutError:
                    return False, (f"<b>失败步骤:</b> 使用 Cookie 验证登录\n<b>选择器:</b> <code>{verify_selector}</code>")

            else: # auth_method == 'form'
                page = context.new_page()
                page.goto(url, timeout=30000)
                username = site_config.get('USER')
                password = site_config.get('PASS')
                pre_login_selector = site_config.get('PRE_LOGIN_CLICK_SELECTOR')
                user_selector = site_config.get('USER_SELECTOR')
                pass_selector = site_config.get('PASS_SELECTOR')
                submit_selector = site_config.get('SUBMIT_SELECTOR')
                
                required_vars = {"USER": username, "PASS": password, "USER_SELECTOR": user_selector, 
                                 "PASS_SELECTOR": pass_selector, "SUBMIT_SELECTOR": submit_selector, 
                                 "VERIFY_SELECTOR": verify_selector}
                missing_vars = [key for key, value in required_vars.items() if not value]
                if missing_vars:
                    return False, f"表单模式缺少配置: <code>{', '.join(missing_vars)}</code>"

                if pre_login_selector:
                    try: page.locator(pre_login_selector).click(timeout=15000)
                    except PlaywrightTimeoutError: return False, (f"<b>失败步骤:</b> 登录前点击\n<b>选择器:</b> <code>{pre_login_selector}</code>")
                try: page.locator(user_selector).fill(username, timeout=15000)
                except PlaywrightTimeoutError: return False, (f"<b>失败步骤:</b> 填写用户名\n<b>选择器:</b> <code>{user_selector}</code>")
                try: page.locator(pass_selector).fill(password, timeout=15000)
                except PlaywrightTimeoutError: return False, (f"<b>失败步骤:</b> 填写密码\n<b>选择器:</b> <code>{pass_selector}</code>")
                try: page.locator(submit_selector).click(timeout=15000)
                except PlaywrightTimeoutError: return False, (f"<b>失败步骤:</b> 点击登录按钮\n<b>选择器:</b> <code>{submit_selector}</code>")
                
                page.wait_for_load_state('domcontentloaded', timeout=20000)

                try:
                    page.locator(verify_selector).wait_for(timeout=15000)
                except PlaywrightTimeoutError:
                    return False, (f"<b>失败步骤:</b> 验证登录成功\n<b>选择器:</b> <code>{verify_selector}</code>")
                
                post_login_selectors_str = site_config.get('POST_LOGIN_CLICK_SELECTORS')
                if post_login_selectors_str:
                    selectors_list = [s.strip() for s in post_login_selectors_str.split(';') if s.strip()]
                    if selectors_list:
                        for i, selector in enumerate(selectors_list, 1):
                            page.wait_for_timeout(30000)
                            try: page.locator(selector).click(timeout=15000)
                            except PlaywrightTimeoutError: return False, (f"<b>失败步骤:</b> 登录后点击 #{i}\n<b>选择器:</b> <code>{selector}</code>")
                        return True, f"成功登录并执行了 {len(selectors_list)} 个登录后点击操作。"
                return True, "成功登录，未配置登录后操作。"

        except Exception as e:
            error_message = f"发生未知错误: <code>{str(e)}</code>"
            if 'page' in locals():
              site_index = site_config.get('id', 'unknown')
              page.screenshot(path=f"/data/site_{site_index}_error.png")
            return False, error_message
        finally:
            browser.close()

def process_single_site(site_index):
    config = load_config()
    target_site = None
    for site in config.get('sites', []):
        if site.get('id') == site_index:
            target_site = site
            break
    
    if not target_site:
        print(f"错误：在 {CONFIG_FILE} 中未找到 ID 为 {site_index} 的网站配置。")
        return

    site_url = target_site.get('URL')
    site_name = target_site.get('NAME', f'网站{site_index}')
    
    success, message = login_to_site(target_site)
    
    if success:
        status_icon, status_text = "✅", "<b>任务成功</b>"
    else:
        status_icon, status_text = "❌", "<b>任务失败</b>"
        
    html_report = (f"<b>- 定时登录任务报告 -</b>\n\n{status_icon} {status_text}\n\n"
                   f"<b>网站名称:</b> {site_name}\n<b>网站地址:</b> <code>{site_url}</code>\n\n"
                   f"<b>详细信息:</b>\n{message}")
                   
    print(f"\n--- 登录任务报告 ---\n{html_report.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', '')}\n--------------------")
    send_telegram_notification(html_report)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            site_id_to_process = int(sys.argv[1])
            process_single_site(site_id_to_process)
        except ValueError:
            sys.exit("错误：提供的参数不是一个有效的数字。")
    else:
        print("未提供特定网站参数，脚本退出。")
