# src/main.py (最终修复版，增加登录后等待页面加载)

import os
import sys
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ... (send_telegram_notification 和其他函数保持不变)
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
    url = os.getenv(f'SITE{site_index}_URL')
    username = os.getenv(f'SITE{site_index}_USER')
    password = os.getenv(f'SITE{site_index}_PASS')
    pre_login_selector = os.getenv(f'SITE{site_index}_PRE_LOGIN_CLICK_SELECTOR')
    user_selector = os.getenv(f'SITE{site_index}_USER_SELECTOR')
    pass_selector = os.getenv(f'SITE{site_index}_PASS_SELECTOR')
    submit_selector = os.getenv(f'SITE{site_index}_SUBMIT_SELECTOR')
    verify_selector = os.getenv(f'SITE{site_index}_VERIFY_SELECTOR')
    post_login_selectors_str = os.getenv(f'SITE{site_index}_POST_LOGIN_CLICK_SELECTORS')
    
    required_vars = {
        "URL": url, "USER": username, "PASS": password,
        "USER_SELECTOR": user_selector, "PASS_SELECTOR": pass_selector,
        "SUBMIT_SELECTOR": submit_selector, "VERIFY_SELECTOR": verify_selector
    }
    missing_vars = [key for key, value in required_vars.items() if not value]
    if missing_vars:
        error_msg = f"缺少以下环境变量: <code>{', '.join(missing_vars)}</code>"
        return False, error_msg

    print(f"开始尝试登录: {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        try:
            page.goto(url, timeout=30000)

            if pre_login_selector:
                print(f"执行登录前点击 (选择器: {pre_login_selector})")
                try:
                    page.locator(pre_login_selector).click(timeout=15000)
                except PlaywrightTimeoutError:
                    return False, (f"<b>失败步骤:</b> 登录前点击\n<b>选择器:</b> <code>{pre_login_selector}</code>")

            print(f"1. 填写用户名 (选择器: {user_selector})")
            try:
                page.locator(user_selector).fill(username, timeout=15000)
            except PlaywrightTimeoutError:
                return False, (f"<b>失败步骤:</b> 填写用户名\n<b>选择器:</b> <code>{user_selector}</code>")

            print(f"2. 填写密码 (选择器: {pass_selector})")
            try:
                page.locator(pass_selector).fill(password, timeout=15000)
            except PlaywrightTimeoutError:
                return False, (f"<b>失败步骤:</b> 填写密码\n<b>选择器:</b> <code>{pass_selector}</code>")

            print(f"3. 点击登录按钮 (选择器: {submit_selector})")
            try:
                page.locator(submit_selector).click(timeout=15000)
            except PlaywrightTimeoutError:
                return False, (f"<b>失败步骤:</b> 点击登录按钮\n<b>选择器:</b> <code>{submit_selector}</code>")

            # --- THE FINAL, DEFINITIVE FIX ---
            # 在点击登录后，我们明确地、耐心地等待页面网络完全空闲，
            # 这标志着所有跳转和动态内容加载都已完成。
            print("   等待页面加载完成...")
            page.wait_for_load_state('networkidle', timeout=40000) # 等待网络空闲，最长40秒
            print("   页面已完全加载。")
            # -----------------------------------

            print(f"4. 验证登录 (等待元素: {verify_selector})")
            try:
                page.locator(verify_selector).wait_for(timeout=15000)
                print("   验证成功！")
            except PlaywrightTimeoutError:
                return False, (f"<b>失败步骤:</b> 验证登录成功\n<b>选择器:</b> <code>{verify_selector}</code>")
            
            # ... (后续的 post-login click 逻辑保持不变)
            if post_login_selectors_str:
                selectors_list = [s.strip() for s in post_login_selectors_str.split(';') if s.strip()]
                if selectors_list:
                    for i, selector in enumerate(selectors_list, 1):
                        print(f"   等待 30 秒后执行点击 {i}/{len(selectors_list)}...")
                        page.wait_for_timeout(30000)
                        print(f"   执行点击 (选择器: {selector})")
                        try:
                            page.locator(selector).click(timeout=15000)
                        except PlaywrightTimeoutError:
                            return False, (f"<b>失败步骤:</b> 登录后点击 #{i}\n<b>选择器:</b> <code>{selector}</code>")
                    success_msg = f"成功登录并执行了 {len(selectors_list)} 个登录后点击操作。"
                else:
                    success_msg = "成功登录，未配置登录后操作。"
            else:
                success_msg = "成功登录，未配置登录后操作。"
            return True, success_msg

        except Exception as e:
            error_message = f"发生未知错误: <code>{str(e)}</code>"
            page.screenshot(path=f"site_{site_index}_error.png")
            return False, error_message
        finally:
            browser.close()

def process_single_site(site_index):
    # ... (此函数内容保持不变)
    site_url = os.getenv(f'SITE{site_index}_URL')
    site_name = os.getenv(f'SITE{site_index}_NAME', f'网站{site_index}')
    success, message = login_to_site(site_index)
    if success:
        status_icon = "✅"
        status_text = "<b>任务成功</b>"
    else:
        status_icon = "❌"
        status_text = "<b>任务失败</b>"
    html_report = (
        f"<b>- 定时登录任务报告 -</b>\n\n"
        f"{status_icon} {status_text}\n\n"
        f"<b>网站名称:</b> {site_name}\n"
        f"<b>网站地址:</b> <code>{site_url}</code>\n\n"
        f"<b>详细信息:</b>\n{message}"
    )
    print("\n--- 登录任务报告 ---")
    print(html_report.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""))
    print("--------------------")
    send_telegram_notification(html_report)


if __name__ == "__main__":
    # ... (此函数内容保持不变)
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
        print("请通过 'python /app/main.py 1' 的方式来测试单个网站。")
