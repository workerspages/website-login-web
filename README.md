# 定时网站自动登录机器人 (Auto-Login Bot)

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/YOUR_REPO_NAME/.github/workflows/docker-build-push.yml?branch=main)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions)

这是一个全自动的、容器化的网站定时登录机器人。它使用 Playwright（无头浏览器）来模拟登录过程，通过 Cron 实现定时任务，并利用 Telegram Bot 发送登录结果通知。

项目通过 GitHub Actions 实现了完整的 CI/CD 流程，当代码推送到 `main` 分支时，会自动构建 Docker 镜像并将其推送到 Docker Hub 和 GitHub Container Registry (ghcr.io)。

## ✨ 主要功能

- **动态定时任务**：支持为每个网站独立设置 Cron 表达式来定义执行时间。
- **多网站支持**：可同时管理多个网站，配置完全通过环境变量隔离。
- **强大的 Playwright 内核**：使用现代化的 Playwright 框架，比 Selenium 更快、更稳定，并内置智能等待机制。
- **实时通知**：通过 Telegram Bot 即时推送每次登录任务的结果（成功或失败）。
- **完全容器化**：使用官方 Playwright 镜像，简化了环境依赖，保证了跨平台的一致性。
- **自动化 CI/CD**：集成 GitHub Actions，实现代码提交后自动构建和发布 Docker 镜像。

## 🛠️ 技术栈

- **核心逻辑**: Python 3.10+
- **浏览器自动化**: Playwright
- **定时任务**: Cron
- **容器化**: Docker
- **CI/CD**: GitHub Actions

## 🚀 如何运作

1.  当 Docker 容器启动时，入口脚本 `entrypoint.sh` 会执行。
2.  该脚本会扫描所有以 `SITE{i}_...` 格式定义的环境变量。
3.  对于每一个配置了 `_CRON` 时间表的网站，脚本会动态生成一条 `cron` 定时任务。
4.  `cron` 服务随后启动，并在指定的时间触发 Python 脚本 `main.py`，并传入网站对应的序号作为参数。
5.  `main.py` 脚本执行指定网站的登录操作，并将结果通过 Telegram Bot 发送出去。

## ⚙️ 使用说明

### 1. 克隆或 Fork 本仓库

首先，将此仓库 Fork 到你自己的 GitHub 账号下，或者直接克隆到本地。

### 2. (核心) 自定义登录逻辑

**这是成功运行此项目的最关键一步！** 每个网站的登录页面结构都不同。你需要修改 `src/main.py` 文件中的 `login_to_site` 函数，以匹配你目标网站的页面元素。

打开 `src/main.py` 并找到以下代码块：

```python
# src/main.py -> login_to_site 函数

# ...
# 1. 找到用户名输入框并输入
# !!! 将 "#username" 替换为实际的 CSS 选择器 !!!
page.locator("#username").fill(username)

# 2. 找到密码输入框并输入
# !!! 将 "#password" 替换为实际的 CSS 选择器 !!!
page.locator("#password").fill(password)

# 3. 找到并点击登录按钮
# !!! 将 'button[type="submit"]' 替换为实际的 CSS 选择器 !!!
page.locator('button[type="submit"]').click()

# 4. 验证登录是否成功
# !!! 将 "#user-profile" 替换为登录成功后才会出现的元素的 CSS 选择器 !!!
page.locator("#user-profile").wait_for(timeout=15000)
# ...
```

**如何找到正确的选择器？**
1.  在 Chrome/Edge/Firefox 浏览器中打开你的目标登录页面。
2.  按下 `F12` 打开开发者工具。
3.  点击工具栏左上角的 "元素选择" 图标（一个箭头指向方框）。
4.  在页面上点击用户名输入框、密码输入框或登录按钮。
5.  在开发者工具的 "Elements" (元素) 面板中，右键点击高亮的代码行，选择 `Copy` -> `Copy selector`。
6.  将复制的选择器粘贴到 `main.py` 中对应的 `page.locator()` 引号内。

### 3. 配置 GitHub Actions Secrets

为了让 GitHub Actions 能够自动推送镜像到 Docker Hub 和 GHCR，你需要在你的 GitHub 仓库中设置以下 Secrets：

进入 `Settings` -> `Secrets and variables` -> `Actions`，点击 `New repository secret`：

-   `DOCKERHUB_USERNAME`: 你的 Docker Hub 用户名。
-   `DOCKERHUB_TOKEN`: 你的 Docker Hub 访问令牌。

`GITHUB_TOKEN` 是由 GitHub Actions 自动提供的，无需手动设置。

### 4. 部署和运行

将修改后的代码推送到 `main` 分支，GitHub Actions 会自动构建镜像。构建成功后，你可以在任何支持 Docker 的服务器上通过以下命令运行容器：

```bash
docker run -d \
  --name my-login-bot \
  --restart always \
  # 在这里配置你的所有环境变量
  # ... (见下方环境变量详解)
  \
  your-dockerhub-username/your-repo-name:latest
```
*请将 `your-dockerhub-username/your-repo-name` 替换为你的实际镜像地址。*

---

## 🔑 环境变量详解

所有配置均通过环境变量注入容器，实现了代码与配置的分离。

### 全局变量

这些变量对所有网站任务生效。

| 变量名 | 是否必须 | 描述 |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | **是** | 你的 Telegram Bot Token。从 [@BotFather](https://t.me/BotFather) 获取。 |
| `TELEGRAM_CHAT_ID` | **是** | 接收通知的 Telegram 用户或频道的 Chat ID。可以通过向机器人 [@userinfobot](https://t.me/userinfobot) 发送消息来获取你的用户 ID。 |

### 网站专属变量

通过数字后缀 `{i}` (从 1 开始) 来定义多个网站。为每个网站配置一组完整的变量。

| 变量名 | 是否必须 | 描述和示例 |
| :--- | :--- | :--- |
| `SITE{i}_URL` | **是** | **网站{i}** 的登录页面 URL。 **示例**: `SITE1_URL="https://github.com/login"` |
| `SITE{i}_USER` | **是** | **网站{i}** 的登录用户名。 **示例**: `SITE1_USER="my-github-user"` |
| `SITE{i}_PASS` | **是** | **网站{i}** 的登录密码。 **示例**: `SITE1_PASS="my-secret-password"` |
| `SITE{i}_CRON` | **是** | **网站{i}** 的 Cron 定时表达式。 **示例**: `SITE1_CRON="0 5 * * *"` (表示每天凌晨 5:00 执行) |

**Cron 表达式格式**: `分 时 日 月 周`
- `*/10 * * * *`: 每 10 分钟
- `0 9 * * 1-5`: 每个工作日（周一至周五）的上午 9:00
- `30 20 1 * *`: 每月 1 号的晚上 8:30

### 完整 `docker run` 示例

以下示例配置了两个不同的网站，使用不同的定时计划，并将通知发送到指定的 Telegram 频道。

```bash
docker run -d \
  --name my-login-bot \
  --restart always \
  \
  # --- 全局 Telegram 配置 ---
  -e TELEGRAM_BOT_TOKEN="12345:ABC-DEF12345" \
  -e TELEGRAM_CHAT_ID="123456789" \
  \
  # --- 网站 1: GitHub，每天凌晨 3:05 执行 ---
  -e SITE1_URL="https://github.com/login" \
  -e SITE1_USER="my-github-user" \
  -e SITE1_PASS="my-github-password" \
  -e SITE1_CRON="5 3 * * *" \
  \
  # --- 网站 2: 另一个网站，每 6 小时执行一次 ---
  -e SITE2_URL="https://another-site.com/auth" \
  -e SITE2_USER="my-other-user" \
  -e SITE2_PASS="another-secret-pass" \
  -e SITE2_CRON="0 */6 * * *" \
  \
  # --- 指定要运行的 Docker 镜像 ---
  # 从 Docker Hub 拉取:
  your-dockerhub-username/your-repo-name:latest
  # 或者从 GHCR 拉取:
  # ghcr.io/your-github-username/your-repo-name:latest
```

## 📄 License

本项目采用 [MIT License](LICENSE) 开源。
