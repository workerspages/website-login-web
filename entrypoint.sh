#!/bin/sh

# entrypoint.sh (真正最终修复版)

echo "正在启动容器，开始动态生成 Cron 任务..."

ENV_FILE="/app/environment.sh"
CRON_FILE="/etc/cron.d/login-cron"

echo "正在将环境变量写入到 ${ENV_FILE}..."
printenv | grep -E '^(SITE|TELEGRAM|TZ)' > "$ENV_FILE"
chmod +r "$ENV_FILE"

> "$CRON_FILE"

i=1
while true; do
    # --- 关键改动在这里 ---
    # 我们使用一种更安全的 eval 模式，只用它来间接获取变量的值，并赋给一个新变量。
    # 这样可以避免在 echo 中执行复杂的、带特殊字符的字符串。
    cron_schedule_var_name="SITE${i}_CRON"
    site_url_var_name="SITE${i}_URL"
    
    # 安全地获取 cron 计划字符串
    eval "cron_schedule=\$$cron_schedule_var_name"
    # 安全地获取 URL 字符串
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

    # 在 echo 命令中，使用双引号将变量包围起来，确保特殊字符 (*) 不被扩展。
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
