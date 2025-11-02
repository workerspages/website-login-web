# Web Auto-Login Project

基于Playwright的Docker无头浏览器项目，定时自动登录多个网站，支持环境变量自定义Crontab和选择器。

## 快速启动
1. 克隆仓库：`git clone https://github.com/your-username/web-login`
2. 构建：`docker build -t web-login .`
3. 运行（示例一站点）：`docker run -d -e TZ=Asia/Shanghai -e SITE1_URL=... -e SITE1_CRONTAB="0 */6 * * *" web-login`

## 环境变量
- SITE1_URL=登录页URL
- SITE1_USERNAME=用户名
- SITE1_PASSWORD=密码
- SITE1_CRONTAB=定时表达式 (e.g., "0 */6 * * *")
- SITE1_USER_SELECTOR=用户名选择器 (可选)
- ... (详见sites_config.py)

日志：/var/log/site1.log

## CI/CD
推送main分支，Actions自动构建多架构镜像到ghcr.io和Docker Hub。
Secrets: DOCKERHUB_USERNAME, DOCKERHUB_TOKEN。
