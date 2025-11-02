# Headless Browser Auto-Login

一个基于Playwright的无头浏览器Docker项目，用于定时自动登录多个网站。支持环境变量自定义站点配置、选择器和独立Crontab。通过GitHub Actions自动构建镜像并推送至ghcr.io和Docker Hub。

## 功能
- 无头Chrome浏览器自动登录，支持CSS/XPath自定义字段。
- 每个站点独立Crontab定时（环境变量定义）。
- 智能元素查找（未提供选择器时自动匹配）。
- 日志输出到/var/log/siteN.log。

## 目录结构
