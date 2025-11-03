#!/bin/sh

# entrypoint.sh (最终修复版，使用 python3 的绝对路径)

echo "正在启动容器，开始动态生成 Cron 任务..."

ENV_FILE="/app/environment.sh"
CRON_FILE="/etc/cron.d/login-cron"

# --- THE FINAL, DEFINITIVE FIX ---
# 1. 自动查找 python3 可执行文件的完整路径
echo "正在查找 python3 的可执行路径..."
PYTHON_EXECUTABLE=$(which python3)

# 2. 检查是否找到了路径，如果没找到则报错退出，增加健壮性
if [ -z "$PYTHON_EXECUTABLE" ]; then
    echo "致命错误: 未能在系统中找到 python3 可执行文件。容器无法启动。"
    exit 1
fi
echo "Python 可执行文件位于: ${PYTHON_EXECUTABLE}"
# -----------------------------------

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
    
    # 3. 在生成 cron 命令时，使用 python3 的完整路径
    echo "${cron_schedule} root . ${ENV_FILE} && ${PYTHON_EXECUTABLE} /app/main.py ${i} >> /var/log/cron.log 2>&1" >> "$CRON_FILE"

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
