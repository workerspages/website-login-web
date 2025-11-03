# Dockerfile

# --- Stage 1: 构建环境 ---
# 使用一个包含构建工具的 Python 基础镜像
FROM python:3.10-slim-buster AS builder

# 设置工作目录
WORKDIR /app

# 安装系统依赖，用于下载 Chrome 和解压 chromedriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 下载并安装 Google Chrome (无头浏览器需要)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 下载并安装对应版本的 ChromeDriver
# 你可以通过 https://googlechromelabs.github.io/chrome-for-testing/ 查找与 Chrome 版本匹配的 chromedriver
# 这里以一个通用版本为例
RUN CHROME_DRIVER_VERSION=$(wget -q -O - "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | grep -oP '"linux64","url":"\K[^"]+' | sed 's|/chrome-linux64.zip||;s|.*/||' | head -n 1) && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64

# --- Stage 2: 运行环境 ---
# 使用一个干净的 Python 镜像
FROM python:3.10-slim-buster

# 设置工作目录
WORKDIR /app

# 从构建阶段复制 Chrome 和 ChromeDriver
COPY --from=builder /etc/apt/sources.list.d/google-chrome.list /etc/apt/sources.list.d/google-chrome.list
COPY --from=builder /usr/local/bin/chromedriver /usr/local/bin/chromedriver

# 安装 Chrome 和 Cron
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    cron \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 Python 脚本
COPY src/main.py .

# 复制并设置 Cron 任务
COPY cronjob /etc/cron.d/login-cron
RUN chmod 0644 /etc/cron.d/login-cron \
    && crontab /etc/cron.d/login-cron

# 创建日志文件，并设置软链接，以便 `docker logs` 可以看到 cron 的输出
RUN touch /var/log/cron.log
RUN ln -sf /proc/1/fd/1 /var/log/cron.log

# 启动 Cron 服务
# 使用 cron -f 在前台运行，这样容器就不会立即退出
CMD ["cron", "-f"]
