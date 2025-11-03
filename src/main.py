# src/main.py (最终修复版，增加反-反爬虫伪装)

import os
import sys
import requests
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ... (send_telegram_notification 函数保持不变)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
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


def login_to_site(site_index):
    auth_method = os.getenv(f'SITE{site_index}_AUTH_METHOD', 'form').lower()
    cookie_str = os.getenv(f'SITE{site_index}_COOKIE')
    url = os.getenv(f'SITE{site_index}_URL')
    verify_selector = os.getenv(f'SITE{site_index}_VERIFY_SELECTOR')

    print(f"开始尝试登录: {url} (模式: {auth_method})")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        try:
            # --- THE ULTIMATE FIX: DISGUISE OUR BOT ---
            # 1. 创建一个自定义的浏览器上下文，而不是直接使用 browser.new_page()
            # 2. 我们设置一个真实的、常见的浏览器 User-Agent，伪装成普通的 Chrome 浏览器
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
            )

            # 3. 在页面加载前，运行一段特殊的 JavaScript 脚本，
            #    将 navigator.webdriver 的值从 true 修改为 false，从而隐藏我们的“机器人”身份。
            context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # -----------------------------------------------

            if auth_method == 'cookie':
                if not cookie_str or not verify_selector:
                    return False, "Cookie 模式需要 <code>SITE{i}_COOKIE</code> 和 <code>SITE{i}_VERIFY_SELECTOR</code>。"
                
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                
                cookies = []
                for cookie_pair in cookie_str.split(';'):
                    if '=' in cookie_pair:
                        name, value = cookie_pair.strip().split('=', 1)
                        cookies.append({'name': name, 'value': value, 'domain': domain, 'path': '/'})
                
                # 在我们伪装好的 context 中添加 Cookie
                context.add_cookies(cookies)
                # 从伪装好的 context 中创建新页面
                page = context.new_page()

                page.goto(url, timeout=30000)
                
                print("Cookie 已注入，正在验证登录状态...")
                try:
                    page.locator(verify_selector).wait_for(timeout=15000)
                    print("   验证成功！")
                    return True, "使用 Cookie 成功认证。"
                except PlaywrightTimeoutError:
                    return False, (f"<b>失败步骤:</b> 使用 Cookie 验证登录\n"
                                   f"<b>选择器:</b> <code>{verify_selector}</code>")

            else: # auth_method == 'form'
                # 对于表单模式，我们也使用这个伪装好的 context
                page = context.new_page()
                page.goto(url, timeout=30000)

                # ... (所有表单填充和点击的逻辑保持完全不变)
                # ...
                return True, "成功登录，未配置登录后操作。" # 简化示例

        except Exception as e:
            error_message = f"发生未知错误: <code>{str(e)}</code>"
            if 'page' in locals():
                page.screenshot(path=f"site_{site_index}_error.png")
            return False, error_message
        finally:
            browser.close()

# ... (process_single_site 和 if __name__ == "__main__" 的内容保持不变)
def process_single_site(site_index):
    site_url = os.getenv(f'SITE{site_index}_URL')
    site_name = os.getenv(f'SITE{site_index}_NAME', f'网站{site_index}')
    success, message = login_to_site(site_index)
    if success: status_icon, status_text = "✅", "<b>任务成功</b>"
    else: status_icon, status_text = "❌", "<b>任务失败</b>"
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
