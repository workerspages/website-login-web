# src/main.py (最终优化版: 模拟人类点击延迟)
import os
import sys
import json
import random
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
    except (FileNotFoundError, json.JSONDecodeError):
        sys.exit(f"错误: 无法加载或解析配置文件 {CONFIG_FILE}。")


def send_telegram_notification(html_message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("警告：未配置 Telegram 的 BOT_TOKEN 或 CHAT_ID，跳过发送通知。")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': html_message, 'parse_mode': 'HTML'}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"发送 Telegram 通知时发生网络错误：{e}")


def login_to_site(site_config):
    auth_method = site_config.get('AUTH_METHOD', 'form').lower()
    cookie_input_str = site_config.get('COOKIE')
    url = site_config.get('URL')
    verify_selector = site_config.get('VERIFY_SELECTOR')

    print(f"开始尝试登录: {url} (模式: {auth_method})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            )
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page = context.new_page()

            if auth_method == 'cookie':
                if not cookie_input_str or not verify_selector:
                    return False, "Cookie 模式需要 <code>COOKIE</code> 和 <code>VERIFY_SELECTOR</code>。"
                
                final_cookies = []
                parsed_url = urlparse(url)
                base_domain = '.'.join(parsed_url.netloc.split('.')[-2:])

                try:
                    print("尝试将 Cookie 解析为 JSON 格式...")
                    cookies_from_json = json.loads(cookie_input_str)
                    if isinstance(cookies_from_json, dict):
                        cookies_from_json = [cookies_from_json]
                    
                    print("JSON 解析成功。正在净化和补全 Cookie...")
                    for cookie in cookies_from_json:
                        if 'domain' not in cookie or not cookie['domain']: cookie['domain'] = f".{base_domain}"
                        if 'path' not in cookie or not cookie['path']: cookie['path'] = '/'
                        if 'sameSite' in cookie and isinstance(cookie['sameSite'], str):
                            capitalized = cookie['sameSite'].capitalize()
                            if capitalized in ['Lax', 'Strict', 'None']:
                                cookie['sameSite'] = capitalized
                            else:
                                del cookie['sameSite']
                        final_cookies.append(cookie)

                except json.JSONDecodeError:
                    print("JSON 解析失败，回退到 key=value; 字符串格式解析...")
                    for pair in cookie_input_str.split(';'):
                        if '=' in pair:
                            name, value = pair.strip().split('=', 1)
                            final_cookies.append({
                                'name': name, 'value': value,
                                'domain': f".{base_domain}", 'path': '/'
                            })

                if not final_cookies:
                    return False, "<b>失败步骤:</b> 解析 Cookie\n<b>错误:</b> 未能从输入中解析出任何有效的 Cookie。"

                context.add_cookies(final_cookies)
                page.goto(url, timeout=30000)
                print("Cookie 已注入，正在验证登录状态...")
            
            else: # auth_method == 'form'
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
            
            # 步骤1: 验证登录 (所有模式共用)
            try:
                print(f"验证登录: 等待元素 '{verify_selector}' 出现...")
                page.locator(verify_selector).wait_for(timeout=20000)
                print("   验证成功！登录状态确认。")
            except PlaywrightTimeoutError:
                return False, (f"<b>失败步骤:</b> 验证登录成功\n<b>选择器:</b> <code>{verify_selector}</code>")
            
            # 步骤2: 执行登录后点击 (所有模式共用)
            post_login_selectors_str = site_config.get('POST_LOGIN_CLICK_SELECTORS')
            if post_login_selectors_str:
                selectors_list = [s.strip() for s in post_login_selectors_str.split(';') if s.strip()]
                if selectors_list:
                    for i, selector in enumerate(selectors_list, 1):
                        print(f"  > 准备执行登录后点击 #{i}: 等待元素 '{selector}' 变得可见且稳定...")
                        try:
                            target_element = page.locator(selector)
                            target_element.wait_for(state='visible', timeout=30000)
                            print(f"  > 元素已可见，执行模拟人类点击...")
                            
                            human_like_delay = random.randint(100, 300)
                            target_element.click(timeout=15000, delay=human_like_delay)

                            print(f"  > 点击操作 #{i} 完成 (延迟: {human_like_delay}ms)。等待页面响应...")
                            page.wait_for_timeout(3000)
                        except PlaywrightTimeoutError:
                            return False, (f"<b>失败步骤:</b> 登录后点击 #{i}\n<b>选择器:</b> <code>{selector}</code>\n<b>错误:</b> 等待元素可见超时。")
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
    target_site = next((site for site in config.get('sites', []) if site.get('id') == site_index), None)
    
    if not target_site:
        print(f"错误：在 {CONFIG_FILE} 中未找到 ID 为 {site_index} 的网站配置。")
        return

    site_url = target_site.get('URL')
    site_name = target_site.get('NAME', f'网站{site_index}')
    success, message = login_to_site(target_site)
    
    status_icon, status_text = ("✅", "<b>任务成功</b>") if success else ("❌", "<b>任务失败</b>")
        
    html_report = (f"<b>- 定时登录任务报告 -</b>\n\n{status_icon} {status_text}\n\n"
                   f"<b>网站名称:</b> {site_name}\n<b>网站地址:</b> <code>{site_url}</code>\n\n"
                   f"<b>详细信息:</b>\n{message}")
                   
    print(f"\n--- 登录任务报告 ---\n{html_report.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', '')}\n--------------------")
    send_telegram_notification(html_report)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            process_single_site(int(sys.argv[1]))
        except ValueError:
            sys.exit("错误：提供的参数不是一个有效的数字。")
    else:
        print("未提供特定网站参数，脚本退出。")
