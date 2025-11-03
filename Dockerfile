# Dockerfile (已修复 tzdata 安装问题)

# 使用微软官方的 Playwright 镜像
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 设置时区环境变量，供后续命令使用
ENV TZ=Asia/Shanghai

# 使用 ARG 设置 DEBIAN_FRONTEND，这可以防止 tzdata 包弹出交互式配置窗口
# 这个 ARG 只在构建期间有效，不会保留在最终镜像中
ARG DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 以非交互模式安装 cron 和 tzdata
RUN apt-get update && apt-get install -y cron tzdata --no-install-recommends && \
    # 配置系统时区
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    # 清理 apt 缓存
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
