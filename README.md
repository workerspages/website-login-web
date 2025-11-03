# Web Auto-Login Project

基于Playwright的Docker无头浏览器项目，定时自动登录多个网站，支持环境变量自定义Crontab和选择器。

## 快速启动
1. 克隆仓库：`git clone https://github.com/your-username/web-login`
2. 构建：`docker build -t web-login .`
3. 运行（示例一站点）：`docker run -d -e TZ=Asia/Shanghai -e SITE1_URL=... -e SITE1_CRONTAB="0 */6 * * *" web-login`

## 环境变量

```
docker run -d \
  --name my-login-bot \
  --restart always \
  # 网站1：设置为每天凌晨 3:05 执行
  -e SITE1_URL="https://example.com/login" \
  -e SITE1_USER="myusername" \
  -e SITE1_PASS="mypassword123" \
  -e SITE1_CRON="5 3 * * *" \
  \
  # 网站2：设置为每个工作日 (周一到周五) 的上午 9:00 执行
  -e SITE2_URL="https://another-site.com/auth" \
  -e SITE2_USER="anotheruser" \
  -e SITE2_PASS="anotherpassword456" \
  -e SITE2_CRON="0 9 * * 1-5" \
  \
  # 网站3：为了测试，设置为每 10 分钟执行一次
  -e SITE3_URL="https://test-site.com/signin" \
  -e SITE3_USER="testuser" \
  -e SITE3_PASS="testpass" \
  -e SITE3_CRON="*/10 * * * *" \
  \
  # Telegram 配置 (保持不变)
  -e TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here" \
  -e TELEGRAM_CHAT_ID="your_telegram_chat_id_here" \
  \
  your-dockerhub-username/your-repo-name:latest
```
