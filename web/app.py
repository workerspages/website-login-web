import os
import json
import subprocess
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
# 强烈建议通过环境变量设置一个更复杂的密钥
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a-very-secret-key') 
CONFIG_FILE = '/data/config.json'
CRON_GENERATOR_SCRIPT = '/usr/local/bin/entrypoint.sh'

# 从环境变量获取登录凭据
ADMIN_USERNAME = os.environ.get('WEB_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('WEB_PASS', 'password')

def get_config():
    """加载 JSON 配置文件，如果不存在则创建一个默认结构"""
    if not os.path.exists(CONFIG_FILE):
        return {'global': {'TELEGRAM_BOT_TOKEN': '', 'TELEGRAM_CHAT_ID': '', 'TZ': 'Asia/Shanghai'}, 'sites': []}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {'global': {'TELEGRAM_BOT_TOKEN': '', 'TELEGRAM_CHAT_ID': '', 'TZ': 'Asia/Shanghai'}, 'sites': []}

def save_config(config):
    """保存配置到 JSON 文件"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def login_required(f):
    """登录装饰器，保护需要登录才能访问的页面"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误!', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        config = get_config()
        # 更新全局设置
        config['global']['TELEGRAM_BOT_TOKEN'] = request.form.get('telegram_bot_token')
        config['global']['TELEGRAM_CHAT_ID'] = request.form.get('telegram_chat_id')
        config['global']['TZ'] = request.form.get('tz')

        # 更新网站设置
        sites = []
        site_indices = sorted(list(set([key.split('_')[0] for key in request.form if key.startswith('site')])))
        
        for index_str in site_indices:
            site_id = int(index_str.replace('site', ''))
            # 只有当 URL 和 CRON 都存在时，才认为这是一个有效的站点配置
            if request.form.get(f'site{site_id}_URL') and request.form.get(f'site{site_id}_CRON'):
                site_data = {
                    'id': site_id,
                    'NAME': request.form.get(f'site{site_id}_NAME', f'网站{site_id}'),
                    'URL': request.form.get(f'site{site_id}_URL'),
                    'CRON': request.form.get(f'site{site_id}_CRON'),
                    'AUTH_METHOD': request.form.get(f'site{site_id}_AUTH_METHOD', 'form'),
                    'USER': request.form.get(f'site{site_id}_USER'),
                    'PASS': request.form.get(f'site{site_id}_PASS'),
                    'COOKIE': request.form.get(f'site{site_id}_COOKIE'),
                    'PRE_LOGIN_CLICK_SELECTOR': request.form.get(f'site{site_id}_PRE_LOGIN_CLICK_SELECTOR'),
                    'USER_SELECTOR': request.form.get(f'site{site_id}_USER_SELECTOR'),
                    'PASS_SELECTOR': request.form.get(f'site{site_id}_PASS_SELECTOR'),
                    'SUBMIT_SELECTOR': request.form.get(f'site{site_id}_SUBMIT_SELECTOR'),
                    'VERIFY_SELECTOR': request.form.get(f'site{site_id}_VERIFY_SELECTOR'),
                    'POST_LOGIN_CLICK_SELECTORS': request.form.get(f'site{site_id}_POST_LOGIN_CLICK_SELECTORS')
                }
                sites.append(site_data)
        
        config['sites'] = sites
        save_config(config)

        # 调用脚本重新生成 cron 任务
        try:
            # 使用 subprocess 调用外部脚本
            result = subprocess.run([CRON_GENERATOR_SCRIPT], capture_output=True, text=True, check=True)
            print("Cron regeneration script output:", result.stdout)
            flash('配置已保存并成功更新定时任务!', 'success')
        except subprocess.CalledProcessError as e:
            print("Error regenerating cron jobs:", e.stderr)
            flash(f'配置已保存，但更新定时任务失败: {e.stderr}', 'danger')
        
        return redirect(url_for('index'))

    config = get_config()
    return render_template('index.html', config=config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
