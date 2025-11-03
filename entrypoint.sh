#!/bin/sh

# entrypoint.sh (修复环境变量导出问题)

echo "正在启动容器，开始动态生成 Cron 任务..."

ENV_FILE="/app/environment.sh"
CRON_FILE="/etc/cron.d/login-cron"

echo "正在将环境变量写入到 ${ENV_FILE}..."
# --- 关键改动在这里 ---
# 我们使用 sed 在每一行的开头加上 'export '，以确保变量能被子进程继承
printenv | grep -E '^(SITE|TELEGRAM|TZ)' | sed 's/^/export /' > "$ENV_FILE"
chmod +r "$ENV_FILE"

# 为了调试，我们打印出文件的内容，确认 'export' 已添加
echo "--- environment.sh content (should start with 'export') ---"
cat "$ENV_FILE"
echo "--------------------------------------------------------"

> "$CRON_FILE"

i=1
while true; do
    cron_schedule_var_name="SITE${i}_CRON"
    site_url_var_name="SITE${i}_URL"
    
    eval "cron_schedule=\$$cron_schedule_var_name"
    eval "site_url=\$$site_url_var_name"

    if [ -z "$cron_schedule" ]; then
        echo "未找到 ${cron_schedule_var_name}，停止搜索更多网站。"
        break
    fi

    if [ -z "$site_url" ]; then
        echo "警告: 找到了 ${cron_schedule_var_name}，但 ${site_url_var_name} 不存在。跳过此任务。"
        i=$((i + 1))
        continue
    fi

    echo "为 网站${i} 添加定时任务: ${cron_schedule}"

    echo "${cron_schedule} . ${ENV_FILE} && python /app/main.py ${i} >> /var/log/cron.log 2>&1" >> "$CRON_FILE"

    i=$((i + 1))
done

if [ -s "$CRON_FILE" ]; then
    chmod 0644 "$CRON_FILE"
    crontab "$CRON_FILE"
else
    echo "警告：没有生成任何有效的 Cron 任务。"
fi

echo "Cron 任务生成完毕。内容如下:"
cat -e "$CRON_FILE"
echo "-----------------------------------"
echo "启动 Cron 服务..."

exec "$@"
