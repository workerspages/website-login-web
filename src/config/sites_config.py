import os
import re
import json

def get_all_site_configs():
    """
    从环境变量中解析所有站点配置，返回字典列表。
    每个站点配置包含URL、凭证、选择器等。
    """
    site_ids = set()
    for key in os.environ:
        match = re.match(r'^SITE(\d+)_URL$', key)
        if match:
            site_ids.add(match.group(1))
    
    configs = []
    for site_id in sorted(site_ids, key=int):
        prefix = f'SITE{site_id}_'
        config = {
            'id': site_id,
            'url': os.getenv(prefix + 'URL'),
            'username': os.getenv(prefix + 'USERNAME'),
            'password': os.getenv(prefix + 'PASSWORD'),
            'user_selector': os.getenv(prefix + 'USER_SELECTOR'),
            'pass_selector': os.getenv(prefix + 'PASS_SELECTOR'),
            'submit_selector': os.getenv(prefix + 'SUBMIT_SELECTOR'),
            'success_selector': os.getenv(prefix + 'SUCCESS_SELECTOR'),
            'success_url_regex': os.getenv(prefix + 'SUCCESS_URL_REGEX'),
            'schedule': os.getenv(prefix + 'SCHEDULE', '0 */6 * * *'),
            'login_action': os.getenv(prefix + 'LOGIN_ACTION', 'click').lower(),
            'wait_for': os.getenv(prefix + 'WAIT_FOR', 'dom_content_loaded'),
            'viewport': os.getenv(prefix + 'VIEWPORT', '1280x800'),
            'headless': os.getenv(prefix + 'HEADLESS', 'true').lower() != 'false',
            'timeout_ms': int(os.getenv(prefix + 'TIMEOUT_MS', '30000')),
            'extra_steps': json.loads(os.getenv(prefix + 'EXTRA_STEPS_JSON', '[]')),
            'headers': json.loads(os.getenv(prefix + 'HEADERS_JSON', '{}'))
        }
        # 跳过无效配置
        if not config['url'] or not config['username'] or not config['password']:
            continue
        configs.append(config)
    
    return configs

# 示例：如果需要硬编码测试配置（生产中移除）
# TEST_CONFIGS = [
#     {
#         'id': '1',
#         'url': 'https://example.com/login',
#         'username': 'testuser',
#         'password': 'testpass',
#         'user_selector': 'css:#username',
#         'pass_selector': 'xpath://input[@type="password"]',
#         'submit_selector': 'css:button[type="submit"]',
#         'success_selector': 'css:.dashboard',
#         'schedule': '0 */6 * * *'
#     }
# ]
