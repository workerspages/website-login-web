# src/main.py (使用 Playwright 重写)

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


def login_to_site(site_name, url, username, password):
    """
    使用 Playwright 无头浏览器登录指定网站。
    代码更简洁，内置自动等待机制。
    """
    print(f"开始尝试登录: {site_name} ({url})")
    
    with sync_playwright() as p:
        # 启动 Chromium 浏览器，headless=True 表示无头模式
        # 在 Docker 容器中，必须添加 --no-sandbox 参数
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = browser.new_page()
        
        try:
            # 导航到目标 URL
            page.goto(url, timeout=30000) # 30秒超时

            # --- 核心登录逻辑 (使用 Playwright API) ---
            # !!! 注意：这是示例逻辑，你需要根据实际网站的 HTML 结构来修改元素定位器 !!!

            # 1. 找到用户名输入框并输入
            # Playwright 的定位器非常强大，可以按角色、标签、文本等定位
            # page.get_by_label("Username").fill(username) # 如果有 <label>
            page.locator("#username").fill(username) # 使用 CSS 选择器
            print("已输入用户名。")

            # 2. 找到密码输入框并输入
            # page.get_by_label("Password").fill(password)
            page.locator("#password").fill(password)
            print("已输入密码。")

            # 3. 找到并点击登录按钮
            # page.get_by_role("button", name="Log in").click() # 按角色和名称
            page.locator('button[type="submit"]').click() # 使用 CSS 选择器
            print("已点击登录按钮。")

            # 4. 验证登录是否成功
            # Playwright 会自动等待元素出现，无需显式 WebDriverWait
            # 等待某个登录后才出现的元素，例如用户头像或欢迎语
            # locator.wait_for() 确保元素在 DOM 中出现
            page.locator("#user-profile").wait_for(timeout=15000) # 15秒超时
            
            print(f"成功登录 {site_name}!")
            return True, f"✅ 成功登录 {site_name}"

        except PlaywrightTimeoutError:
            error_message = f"登录 {site_name} 时超时或未找到元素"
            print(error_message)
            page.screenshot(path=f"{site_name}_error.png")
            return False, f"❌ 登录 {site_name} 失败 (超时)"
        except Exception as e:
            error_message = f"登录 {site_name} 时发生未知错误: {str(e)}"
            print(error_message)
            page.screenshot(path=f"{site_name}_error.png") # 截图帮助调试
            return False, f"❌ 登录 {site_name} 失败"
        finally:
            browser.close()

# `process_single_site`, `process_all_sites` 和 `if __name__ == "__main__"` 部分
# 无需任何修改，因为它们的逻辑是调用 login_to_site，与内部实现无关。
def process_single_site(site_index):
    # ... (此函数内容保持不变)
    site_url = os.getenv(f'SITE{site_index}_URL')
    site_user = os.getenv(f'SITE{site_index}_USER')
    site_pass = os.getenv(f'SITE{site_index}_PASS')
    if not all([site_url, site_user, site_pass]):
        print(f"错误：SITE{site_index} 的配置不完整，无法执行任务。")
        return
    site_name = f"网站{site_index}"
    success, message = login_to_site(site_name, site_url, site_user, site_pass)
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
        # 在这里，我们不再需要一个“执行全部”的功能，因为cron会独立调度
        # 但保留它用于手动测试可能很有用
        print("未提供特定网站参数，脚本退出。")
        print("请通过 'python main.py 1' 的方式来测试单个网站。")
