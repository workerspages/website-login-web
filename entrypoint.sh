#!/bin/sh

# entrypoint.sh (新版: 基于 config.json 生成 cron 任务)

echo "正在根据 /data/config.json 生成 Cron 任务..."

CONFIG_FILE="/data/config.json"
CRON_FILE="/etc/cron.d/login-cron"
ENV_FILE="/app/environment.sh"

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo "警告: 配置文件 $CONFIG_FILE 不存在。跳过 cron 任务生成。"
    # 创建一个空的 cron 文件，以防 cron 服务因缺少文件而出错
    touch "$CRON_FILE"
    chmod 0644 "$CRON_FILE"
    exit 0
fi

# 查找 python3 可执行文件的完整路径
PYTHON_EXECUTABLE=$(which python3)
if [ -z "$PYTHON_EXECUTABLE" ]; then
    echo "致命错误: 未能找到 python3 可执行文件。"
    exit 1
fi

# 清空旧的 cron 和 env 文件
> "$CRON_FILE"
> "$ENV_FILE"

# 从 JSON 中提取全局变量并写入 env 文件
# 我们使用简单的 grep 和 sed，避免在 sh 中引入复杂的 JSON 解析器
grep -o '"TELEGRAM_BOT_TOKEN": "[^"]*"' "$CONFIG_FILE" | sed 's/"TELEGRAM_BOT_TOKEN": "\(.*\)"/export TELEGRAM_BOT_TOKEN=\1/' >> "$ENV_FILE"
grep -o '"TELEGRAM_CHAT_ID": "[^"]*"' "$CONFIG_FILE" | sed 's/"TELEGRAM_CHAT_ID": "\(.*\)"/export TELEGRAM_CHAT_ID=\1/' >> "$ENV_FILE"
grep -o '"TZ": "[^"]*"' "$CONFIG_FILE" | sed 's/"TZ": "\(.*\)"/export TZ=\1/' >> "$ENV_FILE"

echo "--- environment.sh content ---"
cat "$ENV_FILE"
echo "------------------------------"

# 使用 python 来解析 sites 数组并生成 cron 任务
# 这是比 shell 脚本更健壮的方式
python3 -c "
import json
config_file = '$CONFIG_FILE'
cron_file = '$CRON_FILE'
python_executable = '$PYTHON_EXECUTABLE'
env_file = '$ENV_FILE'

try:
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    with open(cron_file, 'w') as f_cron:
        if 'sites' in config and config['sites']:
            for site in config['sites']:
                site_id = site.get('id')
                cron_schedule = site.get('CRON')
                if site_id and cron_schedule:
                    print(f'为 网站{site_id} 添加定时任务: {cron_schedule}')
                    cron_command = f\"{cron_schedule} root . {env_file} && {python_executable} /app/src/main.py {site_id} >> /var/log/cron.log 2>&1\n\"
                    f_cron.write(cron_command)
            f_cron.write('\n') # 文件末尾必须有一个空行
    print('Cron 任务文件已成功创建。')

except Exception as e:
    print(f'生成 Cron 任务时出错: {e}')
"

chmod 0644 "$CRON_FILE"

echo "Cron 任务文件内容如下:"
cat -e "$CRON_FILE"
echo "-----------------------------------"
