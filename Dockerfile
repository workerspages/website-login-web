# Dockerfile (已更新)

# --- Stage 1: 构建环境 (保持不变) ---
FROM python:3.10-slim-buster AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y wget gnupg unzip --no-install-recommends && rm -rf /var/lib/apt/lists/*
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*
RUN CHROME_DRIVER_VERSION=$(wget -q -O - "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json" | grep -oP '"linux64","url":"\K[^"]+' | sed 's|/chrome-linux64.zip||;s|.*/||' | head -n 1) && \
    wget -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_DRIVER_VERSION}/linux64/chromedriver-linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    mv /usr/local/bin/chromedriver-linux64/chromedriver /usr/local/bin/ && \
    rm -rf /tmp/chromedriver.zip /usr/local/bin/chromedriver-linux64

# --- Stage 2: 运行环境 (已更新) ---
FROM python:3.10-slim-buster
WORKDIR /app

# 复制 Chrome 和 ChromeDriver (保持不变)
COPY --from=builder /etc/apt/sources.list.d/google-chrome.list /etc/apt/sources.list.d/google-chrome.list
COPY --from=builder /usr/local/bin/chromedriver /usr/local/bin/chromedriver

# 安装 Chrome 和 Cron (保持不变)
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    cron \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖 (保持不变)
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 Python 脚本
COPY src/main.py .

# ---- 新增和修改的部分 ----
# 复制入口脚本并赋予执行权限
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 创建日志文件并设置软链接 (保持不变)
RUN touch /var/log/cron.log
RUN ln -sf /proc/1/fd/1 /var/log/cron.log

# 设置入口点和默认命令
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["cron", "-f"]
