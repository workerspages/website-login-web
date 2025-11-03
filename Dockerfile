# Dockerfile (最终的完美版本，强制指定浏览器路径)

# 使用微软官方的 Playwright 镜像。
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# --- THE DEFINITIVE FIX ---
# 强制 Playwright 使用由基础镜像提供的、系统级的浏览器安装路径。
# 这会覆盖任何用户级别的缓存或配置，彻底解决 "Executable doesn't exist" 问题。
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 设置时区环境变量
ENV TZ=Asia/Shanghai
# 防止 tzdata 在安装时弹出交互式窗口
ARG DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 以非交互模式安装 cron 和 tzdata
RUN apt-get update && apt-get install -y cron tzdata --no-install-recommends && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并只安装 Python 包。
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
