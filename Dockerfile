# Dockerfile (已更新时区)

# 使用微软官方的 Playwright 镜像
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# --- 新增: 设置默认时区为中国标准时间 ---
ENV TZ=Asia/Shanghai

# 设置工作目录
WORKDIR /app

# 安装 Cron 和 tzdata (用于时区配置)
RUN apt-get update && apt-get install -y cron tzdata --no-install-recommends && \
    # --- 新增: 将系统时区设置为环境变量 TZ 的值 ---
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps

# 复制你的 Python 脚本和入口脚本
COPY src/main.py .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 创建日志文件并设置软链接
RUN touch /var/log/cron.log
RUN ln -sf /proc/1/fd/1 /var/log/cron.log

# 设置入口点和默认命令
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["cron", "-f"]
