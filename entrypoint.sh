#!/bin/bash

# 设置时区
export TZ=${TZ:-Asia/Shanghai}

# 创建日志目录
mkdir -p /var/log

# 安装Playwright浏览器（首次运行）
playwright install --with-deps chromium

# 生成并加载Crontab
python /app/generate_crontab.py

# 启动Cron服务（前台运行，作为PID 1）
exec cron -f
