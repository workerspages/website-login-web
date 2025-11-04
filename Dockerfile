# Dockerfile (新版: 使用 Supervisor 管理 Web UI 和 Cron)

# 1. 基础镜像
FROM python:3.10-slim-bookworm

# 2. 设置环境变量
ENV TZ=Asia/Shanghai
ARG DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 3. 设置工作目录
WORKDIR /app

# 4. 复制依赖文件
COPY src/requirements.txt .

# 5. 安装系统依赖和 Python 依赖
RUN apt-get update && \
    # 安装 supervisor, cron, tzdata
    apt-get install -y supervisor cron tzdata --no-install-recommends && \
    # 安装 Python 依赖
    pip install --no-cache-dir -r requirements.txt && \
    # 安装 Playwright 浏览器
    playwright install --with-deps chromium && \
    # 清理缓存
    rm -rf /var/lib/apt/lists/*

# 6. 配置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 7. 复制应用代码和脚本
COPY src/ ./src
COPY web/ ./web
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod +x /usr/local/bin/entrypoint.sh

# 8. 创建日志文件和数据目录
RUN touch /var/log/cron.log && \
    mkdir -p /data && \
    chown -R www-data:www-data /data
RUN ln -sf /proc/1/fd/1 /var/log/cron.log

# 9. 暴露 Web UI 端口
EXPOSE 8080

# 10. 容器启动时，首先生成一次 cron 任务，然后启动 supervisor
CMD ["/bin/sh", "-c", "/usr/local/bin/entrypoint.sh && /usr/bin/supervisord"]
