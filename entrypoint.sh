#!/bin/sh

# entrypoint.sh

echo "正在启动容器，开始动态生成 Cron 任务..."

# 清空现有的 cron 文件，以防万一
CRON_FILE="/etc/cron.d/login-cron"
> "$CRON_FILE"

# 初始化网站计数器
i=1

# 循环检查环境变量 SITE1_CRON, SITE2_CRON, ...
while true; do
    # 使用 eval 动态获取环境变量的值
    cron_schedule=$(eval echo \$SITE${i}_CRON)
    site_url=$(eval echo \$SITE${i}_URL)

    # 如果这个序号的 CRON 计划不存在，就认为没有更多网站了，退出循环
    if [ -z "$cron_schedule" ]; then
        echo "未找到 SITE${i}_CRON，停止搜索更多网站。"
        break
    fi

    # 检查其他必要的环境变量是否存在
    if [ -z "$site_url" ] || [ -z "$(eval echo \$SITE${i}_USER)" ] || [ -z "$(eval echo \$SITE${i}_PASS)" ]; then
        echo "警告: 找到了 SITE${i}_CRON，但 SITE${i}_URL/USER/PASS 配置不完整。跳过此任务。"
        i=$((i + 1))
        continue
    fi

    # 将 cron 任务行追加到文件中
    # 命令是 'python /app/main.py i'，其中 i 是网站的序号
    echo "为 网站${i} 添加定时任务: ${cron_schedule}"
    echo "${cron_schedule} root python /app/main.py ${i} >> /var/log/cron.log 2>&1" >> "$CRON_FILE"

    # 计数器加一，继续检查下一个网站
    i=$((i + 1))
done

# 设置 cron 文件的正确权限
chmod 0644 "$CRON_FILE"

# 注册 cron 文件
crontab "$CRON_FILE"

echo "Cron 任务生成完毕。内容如下:"
cat "$CRON_FILE"
echo "-----------------------------------"
echo "启动 Cron 服务..."

# 使用 exec "$@" 来执行 Dockerfile CMD 中指定的命令 (即 "cron -f")
exec "$@"
