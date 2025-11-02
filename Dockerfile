FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 安装Cron和工具
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ .

# 复制入口脚本
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh login.py generate_crontab.py

# 创建日志目录
RUN mkdir -p /var/log

ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["./entrypoint.sh"]
