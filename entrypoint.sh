#!/bin/sh

# entrypoint.sh (最终修复版)

echo "正在启动容器，开始动态生成 Cron 任务..."

# 定义环境变量文件的路径
ENV_FILE="/app/environment.sh"
CRON_FILE="/etc/cron.d/login-cron"

# 步骤 1: 将所有需要的环境变量导出到一个文件中
# 我们只导出以 SITE, TELEGRAM, 或 TZ 开头的变量
echo "正在将环境变量写入到 ${ENV_FILE}..."
printenv | grep -E '^(SITE|TELEGRAM|TZ)' > "$ENV_FILE"
# 确保文件是可读的
chmod +r "$ENV_FILE"

# 清空现有的 cron 文件
> "$CRON_FILE"

i=1
while true; do
    # 使用 eval 和双引号来正确读取 cron 计划
    cron_schedule_var="SITE${i}_CRON"
    cron_schedule=$(eval echo "\$$cron_schedule_var")
    
    site_url_var="SITE${i}_URL"
    site_url=$(eval echo "\$$site_url_var")

    if [ -z "$cron_schedule" ]; then
        echo "未找到 ${cron_schedule_var}，停止搜索更多网站。"
        break
    fi

    if [ -z "$site_url" ]; then
        echo "警告: 找到了 ${cron_schedule_var}，但 ${site_url_var} 不存在。跳过此任务。"
        i=$((i + 1))
        continue
    fi

    echo "为 网站${i} 添加定时任务: ${cron_schedule}"

    # 步骤 2: 移除 'root' 用户字段，并让命令先加载环境变量文件
    # '. ${ENV_FILE}' 是 'source ${ENV_FILE}' 的简写，它会加载所有变量到当前 shell
    # '&&' 确保只有在加载成功后才执行 python 脚本
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
