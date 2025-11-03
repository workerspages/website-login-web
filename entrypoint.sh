#!/bin/sh

# entrypoint.sh (最终修复版，使用 python3 命令)

echo "正在启动容器，开始动态生成 Cron 任务..."

ENV_FILE="/app/environment.sh"
CRON_FILE="/etc/cron.d/login-cron"

echo "正在将环境变量写入到 ${ENV_FILE}..."
printenv | grep -E '^(SITE|TELEGRAM|TZ)' \
    | sed 's/="\(.*\)"$/=\1/' \
    | sed 's/=\(.*\)/="\1"/' \
    | sed 's/^/export /' > "$ENV_FILE"
chmod +r "$ENV_FILE"

echo "--- environment.sh content ---"
cat "$ENV_FILE"
echo "------------------------------"

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

    # --- THE FINAL FIX ---
    # 将 'python' 修改为 'python3'，以匹配官方 Python 镜像提供的命令
    echo "${cron_schedule} root . ${ENV_FILE} && python3 /app/main.py ${i} >> /var/log/cron.log 2>&1" >> "$CRON_FILE"

    i=$((i + 1))
done

if [ -s "$CRON_FILE" ]; then
    echo "" >> "$CRON_FILE"
    chmod 0644 "$CRON_FILE"
    echo "Cron 任务文件已成功创建在 /etc/cron.d/ 目录下。"
else
    echo "警告：没有生成任何有效的 Cron 任务。"
fi

echo "Cron 任务文件内容如下:"
cat -e "$CRON_FILE"
echo "-----------------------------------"
echo "启动 Cron 服务..."

exec cron -f -L 15
