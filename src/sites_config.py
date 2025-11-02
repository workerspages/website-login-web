import os
import re
import json

def get_all_site_configs():
    """
    解析所有SITE*环境变量，返回配置字典列表。
    每个配置包含id、url、凭证、选择器、crontab等。
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
            'login_action': os.getenv(prefix + 'LOGIN_ACTION', 'click').lower(),
            'wait_for': os.getenv(prefix + 'WAIT_FOR', 'dom_content_loaded'),
            'viewport': os.getenv(prefix + 'VIEWPORT', '1280x800'),
            'headless': os.getenv(prefix + 'HEADLESS', 'true').lower() != 'false',
            'timeout_ms': int(os.getenv(prefix + 'TIMEOUT_MS', '30000')),
            'extra_steps': json.loads(os.getenv(prefix + 'EXTRA_STEPS_JSON', '[]')),
            'headers': json.loads(os.getenv(prefix + 'HEADERS_JSON', '{}')),
            'crontab': os.getenv(prefix + 'CRONTAB', '0 */6 * * *')  # 新增：独立Crontab
        }
        # 验证基本配置
        if not all([config['url'], config['username'], config['password'], config['crontab']]):
            print(f"[CONFIG] SITE{config['id']} 配置无效（缺少URL/USERNAME/PASSWORD/CRONTAB），跳过")
            continue
        configs.append(config)
    
    return configs

def generate_crontab_lines(configs):
    """
    生成Crontab行列表，每行格式：crontab_expr python /app/login.py site_id >> /var/log/site{id}.log 2>&1
    """
    lines = []
    for config in configs:
        site_id = config['id']
        crontab_expr = config['crontab']
        log_file = f"/var/log/site{site_id}.log"
        line = f"{crontab_expr} python /app/login.py {site_id} >> {log_file} 2>&1"
        lines.append(line)
    # 添加空行以符合Cron格式要求
    lines.append("")
    return lines
