# Dockerfile (最终的"焦土"版, 强制删除所有可能的缓存)

# 使用微软官方的 Playwright 镜像。
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# 1. 强制 Playwright 使用由基础镜像提供的、正确的系统级浏览器安装路径。
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 2. 设置标准时区和非交互式安装模式
ENV TZ=Asia/Shanghai
ARG DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y cron tzdata --no-install-recommends && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装 Python 包
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- THE FINAL, SCORCHED-EARTH FIX ---
# 3. 在构建过程的最后，用最强硬的手段，彻底删除任何可能存在的、
#    由错误缓存引入的、损坏的 Playwright 用户缓存目录。
#    这样，Playwright 将别无选择，只能退回到使用 PLAYWRIGHT_BROWSERS_PATH 指定的正确路径。
RUN rm -rf /root/.cache

# 复制应用程序的其余部分
COPY src/main.py .
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 创建日志文件
RUN touch /var/log/cron.log
RUN ln -sf /proc/1/fd/1 /var/log/cron.log

# 设置入口点和默认命令
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["cron", "-f"]
