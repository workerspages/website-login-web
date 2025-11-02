FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# 安装Chromium和依赖
RUN apt-get update && apt-get install -y \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ .

# 定时任务，使用cron
RUN apt-get update && apt-get install -y cron
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab && crontab /etc/cron.d/crontab

CMD ["cron", "-f"]
