#!/bin/sh

# entrypoint.sh (修复变量值引用问题)

echo "正在启动容器，开始动态生成 Cron 任务..."

ENV_FILE="/app/environment.sh"
CRON_FILE="/etc/cron.d/login-cron"

echo "正在将环境变量写入到 ${ENV_FILE}..."
# --- 关键改动在这里 ---
# 使用 sed 查找第一个等号，并用双引号将等号后面的所有内容包围起来
# 这可以防止 * 等特殊字符在 source 时被 shell 扩展
printenv | grep -E '^(SITE|TELEGRAM|TZ)' | sed 's/=\(.*\)/="\1"/' | sed 's/^/export /' > "$ENV_FILE"
chmod +r "$ENV_FILE"

echo "--- environment.sh content (values should be quoted) ---"
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
