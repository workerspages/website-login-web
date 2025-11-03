# Dockerfile (全新的开始，基于官方 Python 镜像)

# 1. 从一个纯净、稳定、官方的 Python 镜像开始
FROM python:3.10-slim-bookworm

# 2. 设置标准时区和非交互式安装模式
ENV TZ=Asia/Shanghai
ARG DEBIAN_FRONTEND=noninteractive

# 3. 设置工作目录
WORKDIR /app

# 4. 复制依赖文件
COPY src/requirements.txt .

# 5. 一次性完成所有安装，以优化镜像层
RUN apt-get update && \
    # 安装我们需要的系统工具
    apt-get install -y cron tzdata --no-install-recommends && \
    # 安装 Python 依赖
    pip install --no-cache-dir -r requirements.txt && \
    # 关键：让 Playwright 自己安装 Chromium 浏览器及其所需的所有系统依赖
    # --with-deps 会自动运行 apt-get 来安装所有必需的库
    playwright install --with-deps chromium && \
    # 清理 apt 缓存，减小镜像体积
    rm -rf /var/lib/apt/lists/*

# 6. 配置系统时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 7. 复制我们的应用程序代码和脚本
COPY src/main.py .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 8. 创建日志文件
RUN touch /var/log/cron.log
RUN ln -sf /proc/1/fd/1 /var/log/cron.log

# 9. 设置入口点和默认命令
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["cron", "-f"]
