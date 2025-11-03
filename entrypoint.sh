#!/bin/sh

# entrypoint.sh (已修复)

echo "正在启动容器，开始动态生成 Cron 任务..."

CRON_FILE="/etc/cron.d/login-cron"
> "$CRON_FILE"

i=1
while true; do
    # --- 关键改动在这里 ---
    # 旧的命令: cron_schedule=$(eval echo \$SITE${i}_CRON)
    # 新的命令: 通过在变量两侧加上双引号，我们告诉 echo 将其作为单个字符串处理，
    #          从而阻止了 shell 对星号 (*) 的通配符扩展。
    cron_schedule=$(eval echo "\"\$SITE${i}_CRON\"")

    site_url=$(eval echo \$SITE${i}_URL)

    if [ -z "$cron_schedule" ]; then
        echo "未找到 SITE${i}_CRON，停止搜索更多网站。"
        break
    fi

    if [ -z "$site_url" ] || [ -z "$(eval echo \$SITE${i}_USER)" ] || [ -z "$(eval echo \$SITE${i}_PASS)" ]; then
        echo "警告: 找到了 SITE${i}_CRON，但 SITE${i}_URL/USER/PASS 配置不完整。跳过此任务。"
        i=$((i + 1))
        continue
    fi

    echo "为 网站${i} 添加定时任务: ${cron_schedule}"
    echo "${cron_schedule} root python /app/main.py ${i} >> /var/log/cron.log 2>&1" >> "$CRON_FILE"

    i=$((i + 1))
done

# 检查 cron 文件是否为空，如果不为空再尝试安装
if [ -s "$CRON_FILE" ]; then
    chmod 0644 "$CRON_FILE"
    crontab "$CRON_FILE"
else
    echo "警告：没有生成任何有效的 Cron 任务。"
fi

echo "Cron 任务生成完毕。内容如下:"
# 使用 cat -e 来显示隐藏字符，方便调试
cat -e "$CRON_FILE"
echo "-----------------------------------"
echo "启动 Cron 服务..."

exec "$@"
