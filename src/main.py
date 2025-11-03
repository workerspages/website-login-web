# src/main.py (已更新)

import os
import sys
import time
import requests
from selenium import webdriver
# ... (其他 selenium imports 保持不变)
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    # ... (此函数内容保持不变)
    print(f"开始尝试登录: {site_name} ({url})")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        user_field = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        user_field.send_keys(username)
        pass_field = driver.find_element(By.ID, 'password')
        pass_field.send_keys(password)
        login_button = driver.find_element(By.XPATH, '//button[@type="submit"]')
        login_button.click()
        wait.until(EC.presence_of_element_located((By.ID, 'user-profile')))
        print(f"成功登录 {site_name}!")
        return True, f"✅ 成功登录 {site_name}"
    except Exception as e:
        error_message = f"登录 {site_name} 时出错: {str(e)}"
        print(error_message)
        if driver:
            driver.save_screenshot(f"{site_name}_error.png")
        return False, f"❌ 登录 {site_name} 失败"
    finally:
        if driver:
            driver.quit()

def process_single_site(site_index):
    """处理单个指定的网站登录任务"""
    site_url = os.getenv(f'SITE{site_index}_URL')
    site_user = os.getenv(f'SITE{site_index}_USER')
    site_pass = os.getenv(f'SITE{site_index}_PASS')

    if not all([site_url, site_user, site_pass]):
        print(f"错误：SITE{site_index} 的配置不完整，无法执行任务。")
        return

    site_name = f"网站{site_index}"
    success, message = login_to_site(site_name, site_url, site_user, site_pass)
    
    # 单独执行也发送通知
    report_title = f"**定时登录任务报告 (网站{site_index})**"
    print("\n--- 登录任务报告 ---")
    print(message)
    print("--------------------")
    send_telegram_notification(f"{report_title}\n\n{message}")

def process_all_sites():
    """处理所有配置的网站登录任务"""
    all_results = []
    i = 1
    while True:
        site_url = os.getenv(f'SITE{i}_URL')
        if not site_url:
            break
            
        site_user = os.getenv(f'SITE{i}_USER')
        site_pass = os.getenv(f'SITE{i}_PASS')

        if not all([site_user, site_pass]):
            print(f"警告：SITE{i} 的配置不完整，跳过。")
            i += 1
            continue
        
        site_name = f"网站{i}"
        success, message = login_to_site(site_name, site_url, site_user, site_pass)
        all_results.append(message)
        i += 1

    if not all_results:
        print("未找到任何网站配置，程序退出。")
        return

    final_report = "\n".join(all_results)
    report_title = "**定时登录任务报告 (全部)**"
    print("\n--- 登录任务报告 ---")
    print(final_report)
    print("--------------------")
    send_telegram_notification(f"{report_title}\n\n{final_report}")

if __name__ == "__main__":
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        # 如果有参数，例如 "python main.py 1"，则只执行对应的网站任务
        try:
            site_index_to_run = int(sys.argv[1])
            print(f"检测到参数，将只执行网站 {site_index_to_run} 的登录任务...")
            process_single_site(site_index_to_run)
        except ValueError:
            print("错误：提供的参数不是一个有效的数字。")
            sys.exit(1)
    else:
        # 如果没有参数，执行所有网站的登录任务
        print("未提供特定网站参数，将执行所有已配置网站的登录任务...")
        process_all_sites()
