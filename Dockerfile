# Dockerfile (使用 Playwright 镜像 - 大幅简化)

# 使用微软官方的 Playwright 镜像
# 它已经包含了 Python, Playwright 库, 和所有需要的浏览器
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 设置工作目录
WORKDIR /app

# 安装 Cron
# 镜像是基于 Ubuntu Jammy 的，所以我们还是需要安装 cron 服务
RUN apt-get update && apt-get install -y cron --no-install-recommends && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY src/requirements.txt .
# --system 参数确保 playwright 安装的浏览器在系统级别可用
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
