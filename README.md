
# 定时网站自动登录机器人 (带 Web UI 管理面板)

这是一个全自动、**通过 Web 界面轻松配置**的容器化网站定时登录机器人。它使用 Playwright 模拟真实的浏览器操作，通过 Cron 实现定时任务，并利用 Telegram Bot 发送登录结果通知。

与原版最大的不同是，本项目**内置了一个现代化的 Web UI**，您可以在浏览器中完成所有网站的添加、修改和删除，无需再手动编辑环境变量或配置文件，极大地提升了易用性。

![项目截图](https://user-images.githubusercontent.com/12345/67890.png)  
*(请替换为您的项目截图)*

---

## ✨ 主要功能

-   **🖥️ Web 管理面板**: 在浏览器中直观地添加、编辑、删除和管理所有定时任务。
-   **🔐 登录保护**: Web UI 受独立的用户名和密码保护，确保您的配置安全。
-   **🔄 动态任务更新**: 在 Web UI 中保存配置后，系统会自动更新 Cron 定时任务，无需重启容器。
-   **⚙️ 强大的 Playwright 内核**: 使用现代化的 Playwright 框架，比 Selenium 更稳定、更高效，并内置智能等待机制。
-   **🔔 实时通知**: 通过 Telegram Bot 即时推送每次登录任务的结果（成功或失败）。
-   **📦 完全容器化**: 使用 Docker 一键部署，屏蔽了复杂的环境依赖问题。
-   **🚀 自动化 CI/CD**: 集成 GitHub Actions，实现代码提交后自动构建和发布 Docker 镜像。
-   **💪 高度可配置**: 支持表单登录和 Cookie 登录两种模式，并可通过 CSS 选择器适配绝大多数网站的登录流程。
-   **🖱️ 登录后操作**: 支持登录成功后，按顺序连续点击多个页面元素，轻松完成“签到”、“领奖”等组合操作。

## 🚀 部署与运行 (快速开始)

部署本项目非常简单，推荐使用 `docker-compose`。

### 步骤 1: 准备文件

1.  克隆或下载本仓库到您的服务器上。
    ```bash
    git clone https://github.com/your-username/your-repo-name.git
    cd your-repo-name
    ```
2.  在项目根目录（与 `Dockerfile` 同级）下，创建一个 `docker-compose.yml` 文件：

    ```yaml
    # docker-compose.yml
    version: '3.8'

    services:
      website-login:
        image: ghcr.io/workerspages/website-login:latest # 建议替换为您自己构建的镜像
        container_name: website-login
        restart: unless-stopped
        ports:
          # 将容器的 8080 端口映射到您服务器的某个端口，例如 8080
          # 格式: <服务器端口>:<容器端口>
          - "8080:8080"
        volumes:
          # 挂载一个本地目录到容器的 /data 目录
          # 用于持久化存储您的所有网站配置和错误截图
          - ./data:/data
        environment:
          # --- Web UI 登录凭据 (请务必修改) ---
          - WEB_USER=admin
          - WEB_PASS=your_strong_password_123

          # --- Flask 安全密钥 (请务必修改为一个随机长字符串) ---
          # 可以使用命令 `python3 -c 'import secrets; print(secrets.token_hex(24))'` 生成
          - FLASK_SECRET_KEY=your_very_long_random_secret_string

          # --- 容器默认时区 (也可以在 Web UI 中修改) ---
          - TZ=Asia/Shanghai
    ```

### 步骤 2: 启动容器

在 `docker-compose.yml` 文件所在的目录下，运行以下命令启动容器：

```bash
docker-compose up -d
```

第一次启动时，Docker 会自动拉取或构建镜像。

### 步骤 3: 开始配置

1.  **访问 Web UI**: 打开浏览器，访问 `http://<您的服务器IP>:8080` (如果您修改了端口，请使用您设置的端口)。
2.  **登录**: 使用您在 `docker-compose.yml` 中设置的 `WEB_USER` 和 `WEB_PASS` 登录。
3.  **配置任务**:
    *   在“全局配置”中填入您的 Telegram Bot Token 和 Chat ID。
    *   点击“添加一个新网站”按钮。
    *   在弹出的卡片中，填写该网站的所有登录信息（URL、Cron 表达式、认证方式、CSS 选择器等）。
    *   重复此步骤以添加更多网站。
4.  **保存**: 点击页面最下方的“保存所有配置并更新任务”按钮。系统将保存您的配置并立即应用新的定时任务。

至此，您的自动登录机器人已经开始工作了！

---

## 🔑 配置项详解 (Web UI)

所有配置都在 Web UI 中完成，这里对每个字段进行详细说明。

### 全局配置

| 字段名 | 是否必须 | 描述 |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | **是** | 你的 Telegram Bot Token。 |
| `TELEGRAM_CHAT_ID` | **是** | 接收通知的 Telegram 用户或频道的 Chat ID。 |
| `TZ` (时区) | 否 | 设置容器的系统时区，Cron 的执行时间以此为准。默认为 `Asia/Shanghai`。 |

### 网站配置

每个网站都是一张独立的配置卡片。

#### 基础信息

| 字段名 | 是否必须 | 描述和示例 |
| :--- | :--- | :--- |
| **名称 (NAME)** | 否 | 自定义名称，用于在 Telegram 通知中显示，使其更易辨认。 |
| **登录URL\*** | **是** | 网站的登录页面 URL。 **示例**: `https://github.com/login` |
| **CRON表达式\***| **是** | 定义任务的执行时间。**格式**: `分 时 日 月 周`。**示例**: `0 3 * * *` (每天凌晨3点)。 |
| **认证方式** | **是** | 选择 `表单 (form)` 或 `Cookie`。界面会根据您的选择动态显示/隐藏对应的参数区域。 |

#### 表单登录参数 (当认证方式为 `form` 时)

| 字段名 | 是否必须 | 描述 |
| :--- | :--- | :--- |
| **用户名 (USER)** | **是** | 登录账号。 |
| **密码 (PASS)** | **是** | 登录密码。 |
| **登录前点击选择器** | 否 | 用于点击页面上某个元素后才出现登录框的场景 (例如点击“登录”按钮)。 |
| **用户名选择器** | **是** | 用户名输入框的 CSS 选择器。 |
| **密码选择器** | **是** | 密码输入框的 CSS 选择器。 |
| **提交按钮选择器** | **是** | 登录/提交按钮的 CSS 选择器。 |

#### Cookie 登录参数 (当认证方式为 `cookie` 时)

| 字段名 | 是否必须 | 描述 |
| :--- | :--- | :--- |
| **COOKIE** | **是** | 从浏览器中获取的完整 Cookie 字符串。 |

#### 通用参数

| 字段名 | 是否必须 | 描述和示例 |
| :--- | :--- | :--- |
| **登录成功验证选择器** | **是** | 一个**只在登录成功后才会出现**的元素的 CSS 选择器，用于判断任务是否成功。 **示例**: ` .user-avatar` (用户头像) |
| **登录后点击选择器** | 否 | 支持按顺序连续点击。将多个 CSS 选择器用分号 (`;`) 分隔。<br>**应用场景**: 登录后需要先“关闭弹窗”，再点击“每日签到”。<br>**示例**: `#close-popup-btn; .daily-check-in-btn` |

---

## 🎯 如何获取 CSS 选择器？

这是配置中最关键的一步。

1.  在 Chrome/Edge/Firefox 浏览器中打开目标网站，并登录。
2.  按下 `F12` 打开“开发者工具”。
3.  点击工具栏左上角的“元素选择”图标（一个箭头指向方框）。
4.  在页面上点击您想定位的元素（例如用户名输入框、登录按钮、或登录成功后的用户头像）。
5.  在开发者工具的 "Elements" (元素) 面板中，右键点击高亮的代码行。
6.  选择 `Copy` -> `Copy selector`。
7.  将复制的内容粘贴到 Web UI 中对应的输入框即可。

## 👨‍💻 开发者信息

### 技术栈

-   **后端**: Flask + Gunicorn
-   **前端**: Bootstrap 5 + 原生 JavaScript
-   **自动化核心**: Playwright
-   **定时任务**: Cron
-   **进程管理**: Supervisor
-   **容器化**: Docker

### 项目结构

```
.
├── data/                  # (运行时生成) 持久化数据目录，存储 config.json 和截图
├── src/                   # 核心 Python 脚本
│   ├── main.py            # Playwright 登录执行脚本
│   └── requirements.txt   # Python 依赖
├── web/                   # Flask Web 应用
│   ├── static/            # CSS 样式文件
│   ├── templates/         # HTML 模板文件
│   └── app.py             # Web 应用后端逻辑
├── .github/workflows/     # GitHub Actions CI/CD 配置
├── docker-compose.yml     # (需手动创建) Docker Compose 部署文件
├── Dockerfile             # Docker 镜像构建文件
├── entrypoint.sh          # 容器入口脚本，负责生成 Cron 任务
└── supervisord.conf       # Supervisor 进程管理配置
```

### CI/CD

本项目已配置 GitHub Actions (`.github/workflows/docker-build-push.yml`)。当您将代码推送到 `main` 分支时，它会自动执行以下操作：

1.  构建 Docker 镜像。
2.  推送到 Docker Hub。
3.  推送到 GitHub Container Registry (GHCR)。

如果您 Fork 了本仓库，请在您的仓库 `Settings` -> `Secrets and variables` -> `Actions` 中设置以下 Secrets 以启用自动推送：

-   `DOCKERHUB_USERNAME`: 您的 Docker Hub 用户名。
-   `DOCKERHUB_TOKEN`: 您的 Docker Hub 访问令牌。

## 许可证

本项目采用 [MIT License](LICENSE) 开源。
