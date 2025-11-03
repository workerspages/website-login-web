# src/main.py (已更新，支持登录后连续点击)

import os
import sys
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# --- Telegram 通知配置 (保持不变) ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_notification(message):
    # ... (此函数内容保持不变)
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("警告：未配置 Telegram 的 BOT_TOKEN 或 CHAT_ID，跳过发送通知。")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"发送 Telegram 通知失败：{response.text}")
    except Exception as e:
        print(f"发送 Telegram 通知时发生网络错误：{e}")


def login_to_site(site_index):
    """
    使用 Playwright 登录网站，支持登录后执行一系列连续的点击操作。
    """
    site_name = f"网站{site_index}"
    
    # --- 从环境变量加载所有配置 ---
    url = os.getenv(f'SITE{site_index}_URL')
    username = os.getenv(f'SITE{site_index}_USER')
    password = os.getenv(f'SITE{site_index}_PASS')
    
    user_selector = os.getenv(f'SITE{site_index}_USER_SELECTOR')
    pass_selector = os.getenv(f'SITE{site_index}_PASS_SELECTOR')
    submit_selector = os.getenv(f'SITE{site_index}_SUBMIT_SELECTOR')
    verify_selector = os.getenv(f'SITE{site_index}_VERIFY_SELECTOR')
    
    # 新增：加载由分号分隔的连续点击选择器字符串
    post_login_selectors_str = os.getenv(f'SITE{site_index}_POST_LOGIN_CLICK_SELECTORS')

    # --- 验证必要的配置是否存在 ---
    required_vars = {
        "URL": url, "USER": username, "PASS": password,
        "USER_SELECTOR": user_selector, "PASS_SELECTOR": pass_selector,
        "SUBMIT_SELECTOR": submit_selector, "VERIFY_SELECTOR": verify_selector
    }
    
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        error_msg = f"❌ 登录 {site_name} 失败: 缺少以下环境变量: {', '.join(missing_vars)}"
        print(error_msg)
        return False, error_msg

    print(f"开始尝试登录: {site_name} ({url})")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=30000)

            # ... (登录逻辑保持不变)
            print(f"1. 查找用户名输入框 (选择器: {user_selector})")
            page.locator(user_selector).fill(username)
            print("   已输入用户名。")
            print(f"2. 查找密码输入框 (选择器: {pass_selector})")
            page.locator(pass_selector).fill(password)
            print("   已输入密码。")
            print(f"3. 查找并点击登录按钮 (选择器: {submit_selector})")
            page.locator(submit_selector).click()
            print("   已点击登录按钮。")
            print(f"4. 验证登录成功 (等待元素: {verify_selector})")
            page.locator(verify_selector).wait_for(timeout=15000)
            print("   验证元素已出现。登录成功！")
            
            # --- 新增：执行登录后的连续点击操作 ---
            if post_login_selectors_str:
                # 按分号分割字符串，并去除每个选择器前后的空格
                selectors_list = [s.strip() for s in post_login_selectors_str.split(';') if s.strip()]
                
                if selectors_list:
                    print(f"检测到 {len(selectors_list)} 个登录后连续点击任务。")
                    
                    for i, selector in enumerate(selectors_list, 1):
                        print(f"   ---步骤 {i}/{len(selectors_list)}---")
                        print(f"   等待 10 秒...")
                        page.wait_for_timeout(10000)
                        
                        print(f"   执行点击 (选择器: {selector})")
                        page.locator(selector).click()
                        print(f"   点击成功。")
                    
                    success_msg = f"✅ 成功登录 {site_name} 并执行了 {len(selectors_list)} 个登录后点击操作。"
                else:
                    success_msg = f"✅ 成功登录 {site_name}"
            else:
                success_msg = f"✅ 成功登录 {site_name}"

            print(success_msg)
            return True, success_msg

        except PlaywrightTimeoutError:
            error_message = f"❌ 登录 {site_name} 失败: 超时或未找到元素。请检查你的选择器配置是否正确。"
            print(error_message)
            page.screenshot(path=f"{site_name}_error.png")
            return False, error_message
        except Exception as e:
            error_message = f"❌ 登录 {site_name} 失败: 发生未知错误: {str(e)}"
            print(error_message)
            page.screenshot(path=f"{site_name}_error.png")
            return False, error_message
        finally:
            browser.close()

# `process_single_site` 和 `if __name__ == "__main__"` 部分保持不变
def process_single_site(site_index):
    success, message = login_to_site(site_index)
    report_title = f"**定时登录任务报告 (网站{site_index})**"
    print("\n--- 登录任务报告 ---")
    print(message)
    print("--------------------")
    send_telegram_notification(f"{report_title}\n\n{message}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            site_index_to_run = int(sys.argv[1])
            print(f"检测到参数，将只执行网站 {site_index_to_run} 的登录任务...")
            process_single_site(site_index_to_run)
        except ValueError:
            print("错误：提供的参数不是一个有效的数字。")
            sys.exit(1)
    else:
        print("未提供特定网站参数，脚本退出。")
        print("请通过 'python main.py 1' 的方式来测试单个网站。")
