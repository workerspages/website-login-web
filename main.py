import asyncio
import os
import re
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from sites_config import get_all_site_configs  # 导入配置解析

async def parse_selector(page, selector):
    """解析CSS或XPath选择器"""
    if not selector:
        return None
    if selector.startswith('css:'):
        return page.locator(selector[4:]).first
    if selector.startswith('xpath:'):
        return page.locator(f'xpath={selector[6:]}').first
    # 默认CSS
    return page.locator(selector).first

async def smart_find_username(page):
    """智能查找用户名输入框"""
    candidates = [
        "input[autocomplete='username']",
        "input[name*='user' i]",
        "input[id*='user' i]",
        "input[name*='email' i]",
        "input[type='email']",
        "input[placeholder*='user' i]",
        "input[placeholder*='邮箱' i]",
        "input[placeholder*='账号' i]",
    ]
    for candidate in candidates:
        element = page.locator(candidate).first
        if await element.count() > 0:
            return element
    return None

async def smart_find_password(page):
    """智能查找密码输入框"""
    candidates = [
        "input[autocomplete='current-password']",
        "input[type='password']",
        "input[name*='pass' i]",
        "input[id*='pass' i]",
        "input[placeholder*='密码' i]",
    ]
    for candidate in candidates:
        element = page.locator(candidate).first
        if await element.count() > 0:
            return element
    return None

async def smart_find_submit(page):
    """智能查找提交按钮"""
    candidates = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('登录')",
        "button:has-text('登入')",
        "button:has-text('Log in')",
        "button:has-text('Sign in')",
    ]
    for candidate in candidates:
        element = page.locator(candidate).first
        if await element.count() > 0:
            return element
    return None

async def login_site(config):
    """执行单个站点登录"""
    site_id = config['id']
    url = config['url']
    username = config['username']
    password = config['password']
    user_selector = config['user_selector']
    pass_selector = config['pass_selector']
    submit_selector = config['submit_selector']
    success_selector = config['success_selector']
    success_url_regex = config['success_url_regex']
    login_action = config['login_action']
    wait_for = config['wait_for']
    viewport = config['viewport']
    headless = config['headless']
    timeout = config['timeout_ms']
    extra_steps = config['extra_steps']
    headers = config['headers']

    if not all([url, username, password]):
        print(f"[SITE{site_id}] 配置无效，跳过")
        return

    width, height = map(int, viewport.split('x'))

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless, args=['--no-sandbox', '--disable-dev-shm-usage'])
        context = await browser.new_context(
            viewport={'width': width, 'height': height},
            extra_http_headers=headers
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=timeout)
            if wait_for == 'network_idle':
                await page.wait_for_load_state('networkidle', timeout=timeout)

            # 填充用户名
            user_element = await parse_selector(page, user_selector) or await smart_find_username(page)
            if not user_element or await user_element.count() == 0:
                raise RuntimeError("未找到用户名输入框")
            await user_element.fill(username, timeout=timeout)

            # 填充密码
            pass_element = await parse_selector(page, pass_selector) or await smart_find_password(page)
            if not pass_element or await pass_element.count() == 0:
                raise RuntimeError("未找到密码输入框")
            await pass_element.fill(password, timeout=timeout)

            # 执行额外步骤
            for step in extra_steps:
                if 'click' in step:
                    click_elem = page.locator(step['click']).first
                    if await click_elem.count() > 0:
                        await click_elem.click(timeout=timeout)
                if 'wait_selector' in step:
                    wait_elem = page.locator(step['wait_selector']).first
                    await wait_elem.wait_for(timeout=timeout)

            # 提交登录
            submit_element = await parse_selector(page, submit_selector) or await smart_find_submit(page)
            if not submit_element or await submit_element.count() == 0:
                if login_action == 'press_enter':
                    await pass_element.press('Enter')
                else:
                    raise RuntimeError("未找到提交按钮")
            else:
                if login_action == 'press_enter':
                    await pass_element.press('Enter')
                elif login_action == 'form_submit':
                    await page.evaluate('''(btn) => { if (btn.form && btn.form.submit) btn.form.submit(); }''', await submit_element.element_handle())
                else:
                    await submit_element.click(timeout=timeout)

            # 判定登录成功
            success = False
            if success_selector:
                success_elem = await parse_selector(page, success_selector)
                if success_elem:
                    await success_elem.wait_for(timeout=timeout)
                    success = True
            if not success and success_url_regex:
                pattern = re.compile(success_url_regex)
                for _ in range(20):  # 等待5秒
                    if pattern.search(page.url):
                        success = True
                        break
                    await page.wait_for_timeout(250)
            if not success:
                # 兜底检查常见成功元素
                maybe_success = page.locator("text=退出, text=个人中心, text=Profile, text=Dashboard").first
                if await maybe_success.count() > 0:
                    success = True

            print(f"[SITE{site_id}] 登录{'成功' if success else '可能失败'}，当前URL: {page.url}")
        except PWTimeout as e:
            print(f"[SITE{site_id}] 超时错误: {e}")
        except Exception as e:
            print(f"[SITE{site_id}] 异常: {e}")
        finally:
            await context.close()
            await browser.close()

async def run_once():
    """一次性执行所有站点登录"""
    configs = get_all_site_configs()
    tasks = [login_site(config) for config in configs]
    await asyncio.gather(*tasks)

def setup_scheduler():
    """设置定时任务调度器"""
    configs = get_all_site_configs()
    scheduler = AsyncIOScheduler(timezone=os.getenv('TZ', 'Asia/Shanghai'))
    for config in configs:
        site_id = config['id']
        schedule = config['schedule']
        parts = schedule.split()
        if len(parts) != 5:
            print(f"[SITE{site_id}] 无效调度表达式，跳过")
            continue
        minute, hour, day, month, weekday = parts
        scheduler.add_job(
            lambda sid=site_id: asyncio.create_task(login_site(configs[int(sid)-1])),
            'cron',
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=weekday,
            id=f'site_{site_id}'
        )
    scheduler.start()
    return scheduler

if __name__ == '__main__':
    use_scheduler = os.getenv('USE_SCHEDULER', 'false').lower() == 'true'
    if not use_scheduler:
        asyncio.run(run_once())
    else:
        scheduler = setup_scheduler()
        try:
            asyncio.get_event_loop().run_forever()
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
