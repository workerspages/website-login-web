# src/main.py

import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Telegram 通知配置 ---
# 从环境变量获取 Telegram 配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_notification(message):
    """发送消息到指定的 Telegram 频道"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("警告：未配置 Telegram 的 BOT_TOKEN 或 CHAT_ID，跳过发送通知。")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"发送 Telegram 通知失败：{response.text}")
    except Exception as e:
        print(f"发送 Telegram 通知时发生网络错误：{e}")

def login_to_site(site_name, url, username, password):
    """
    使用 Selenium 无头浏览器登录指定网站。
    注意：此函数中的定位器 (By.ID) 需要根据你的目标网站进行修改。
    """
    print(f"开始尝试登录: {site_name} ({url})")
    
    # --- Selenium WebDriver 配置 ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox") # 在容器中运行的必要设置
    chrome_options.add_argument("--disable-dev-shm-usage") # 解决部分容器资源限制问题
    chrome_options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # --- 核心登录逻辑 ---
        # !!! 注意：这是示例逻辑，你需要根据实际网站的 HTML 结构来修改元素定位器 !!!
        # 使用 WebDriverWait 确保元素已加载
        wait = WebDriverWait(driver, 15)
        
        # 1. 找到用户名输入框并输入
        user_field = wait.until(EC.presence_of_element_located((By.ID, 'username'))) # 示例 ID
        user_field.send_keys(username)
        print("已输入用户名。")

        # 2. 找到密码输入框并输入
        pass_field = driver.find_element(By.ID, 'password') # 示例 ID
        pass_field.send_keys(password)
        print("已输入密码。")

        # 3. 找到并点击登录按钮
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]') # 示例 XPATH
        login_button.click()
        print("已点击登录按钮。")

        # 4. 验证登录是否成功
        # 等待某个登录后才出现的元素，例如用户头像或欢迎语
        wait.until(EC.presence_of_element_located((By.ID, 'user-profile'))) # 示例 ID
        
        print(f"成功登录 {site_name}!")
        return True, f"✅ 成功登录 {site_name}"

    except Exception as e:
        error_message = f"登录 {site_name} 时出错: {str(e)}"
        print(error_message)
        # 错误时截图保存，方便调试 (在容器中可能需要映射卷才能看到)
        driver.save_screenshot(f"{site_name}_error.png")
        return False, f"❌ 登录 {site_name} 失败"
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    all_results = []
    # 循环检查环境变量，支持多个网站 (SITE1, SITE2, ...)
    i = 1
    while True:
        site_url = os.getenv(f'SITE{i}_URL')
        site_user = os.getenv(f'SITE{i}_USER')
        site_pass = os.getenv(f'SITE{i}_PASS')

        if not all([site_url, site_user, site_pass]):
            # 如果 SITEi_URL 不存在，就认为没有更多网站了
            if not site_url:
                break
            else:
                print(f"警告：SITE{i} 的配置不完整，跳过。")
                i += 1
                continue
        
        site_name = f"网站{i}"
        success, message = login_to_site(site_name, site_url, site_user, site_pass)
        all_results.append(message)
        
        i += 1

    if not all_results:
        print("未找到任何网站配置，程序退出。")
        sys.exit(0)

    # --- 发送最终报告 ---
    final_report = "\n".join(all_results)
    print("\n--- 登录任务报告 ---")
    print(final_report)
    print("--------------------")
    send_telegram_notification(f"**定时登录任务报告**\n\n{final_report}")
