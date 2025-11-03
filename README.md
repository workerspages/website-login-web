
# 定时网站自动登录机器人 (Auto-Login Bot)

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/YOUR_REPO_NAME/.github/workflows/docker-build-push.yml?branch=main)](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/actions)

这是一个全自动的、**高度可配置**的、容器化的网站定时登录机器人。它使用 Playwright（无头浏览器）来模拟登录过程，通过 Cron 实现定时任务，并利用 Telegram Bot 发送登录结果通知。

**此项目的最大特点是不需要修改任何代码**。你可以通过设置环境变量来适配几乎所有拥有标准登录流程的网站。

## ✨ 主要功能

- **动态登录流程**：无需修改代码！通过环境变量定义登录所需的 **CSS 选择器**，适配不同网站的页面结构。
- **动态定时任务**：支持为每个网站独立设置 Cron 表达式来定义执行时间。
- **多网站支持**：可同时管理多个网站，配置完全通过环境变量隔离。
- **强大的 Playwright 内核**：使用现代化的 Playwright 框架，比 Selenium 更快、更稳定，并内置智能等待机制。
- **实时通知**：通过 Telegram Bot 即时推送每次登录任务的结果（成功或失败）。
- **完全容器化**：使用官方 Playwright 镜像，简化了环境依赖，保证了跨平台的一致性。
- **自动化 CI/CD**：集成 GitHub Actions，实现代码提交后自动构建和发布 Docker 镜像。

## 🚀 如何运作

1.  当 Docker 容器启动时，入口脚本 `entrypoint.sh` 会执行。
2.  该脚本会扫描所有以 `SITE{i}_...` 格式定义的环境变量。
3.  对于每一个配置了 `_CRON` 时间表的网站，脚本会动态生成一条 `cron` 定时任务。
4.  `cron` 服务随后启动，并在指定的时间触发 Python 脚本 `main.py`，并传入网站对应的序号作为参数。
5.  `main.py` 脚本加载该序号对应的**所有环境变量**（包括 URL、账号、密码以及 CSS 选择器），执行一个完全由配置驱动的登录流程，并将结果通过 Telegram Bot 发送出去。

## ⚙️ 使用说明

### 1. 克隆或 Fork 本仓库

首先，将此仓库 Fork 到你自己的 GitHub 账号下，或者直接克隆到本地。

### 2. 获取目标网站的 CSS 选择器

这是成功运行此项目的最关键一步。你需要找到目标网站登录页面上四个关键元素的 CSS 选择器：

1.  **用户名字段**
2.  **密码字段**
3.  **登录/提交按钮**
4.  **一个只在登录成功后才会出现的元素** (用于验证登录是否成功，例如用户头像、欢迎语、仪表盘标题等)

**如何找到正确的选择器？**
1.  在 Chrome/Edge/Firefox 浏览器中打开你的目标登录页面。
2.  按下 `F12` 打开开发者工具。
3.  点击工具栏左上角的 "元素选择" 图标（一个箭头指向方框）。
4.  在页面上点击你想定位的元素（例如用户名输入框）。
5.  在开发者工具的 "Elements" (元素) 面板中，右键点击高亮的代码行，选择 `Copy` -> `Copy selector`。
6.  将复制的选择器保存下来，等下填入环境变量中。对上述四个关键元素重复此操作。

### 3. 配置 GitHub Actions Secrets

为了让 GitHub Actions 能够自动推送镜像，你需要在你的 GitHub 仓库中设置以下 Secrets：

进入 `Settings` -> `Secrets and variables` -> `Actions`，点击 `New repository secret`：

-   `DOCKERHUB_USERNAME`: 你的 Docker Hub 用户名。
-   `DOCKERHUB_TOKEN`: 你的 Docker Hub 访问令牌。

### 4. 部署和运行

将代码推送到 `main` 分支，GitHub Actions 会自动构建镜像。构建成功后，你可以在任何支持 Docker 的服务器上通过以下命令运行容器：

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

| 变量名 | 是否必须 | 描述 |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | **是** | 你的 Telegram Bot Token。 |
| `TELEGRAM_CHAT_ID` | **是** | 接收通知的 Telegram 用户或频道的 Chat ID。 |

### 网站专属变量

通过数字后缀 `{i}` (从 1 开始) 来定义多个网站。为每个网站配置一组完整的变量。

#### 基础信息

| 变量名 | 是否必须 | 描述和示例 |
| :--- | :--- | :--- |
| `SITE{i}_URL` | **是** | **网站{i}** 的登录页面 URL。 **示例**: `SITE1_URL="https://github.com/login"` |
| `SITE{i}_USER` | **是** | **网站{i}** 的登录用户名。 **示例**: `SITE1_USER="my-github-user"` |
| `SITE{i}_PASS` | **是** | **网站{i}** 的登录密码。 **示例**: `SITE1_PASS="my-secret-password"` |
| `SITE{i}_CRON` | **是** | **网站{i}** 的 Cron 定时表达式。 **示例**: `SITE1_CRON="0 5 * * *"` |

#### 登录流程变量 (CSS Selectors)

| 变量名 | 是否必须 | 描述和示例 |
| :--- | :--- | :--- |
| `SITE{i}_USER_SELECTOR` | **是** | **网站{i}** 用户名输入框的 CSS 选择器。 **示例**: `SITE1_USER_SELECTOR="#login_field"` |
| `SITE{i}_PASS_SELECTOR` | **是** | **网站{i}** 密码输入框的 CSS 选择器。 **示例**: `SITE1_PASS_SELECTOR="#password"` |
| `SITE{i}_SUBMIT_SELECTOR` | **是** | **网站{i}** 登录/提交按钮的 CSS 选择器。 **示例**: `SITE1_SUBMIT_SELECTOR="input[name='commit']"` |
| `SITE{i}_VERIFY_SELECTOR` | **是** | **网站{i}** 登录成功后页面的验证元素的 CSS 选择器。 **示例**: `SITE1_VERIFY_SELECTOR=".AppHeader-user .avatar"` (GitHub 登录后的用户头像) |

### 完整 `docker run` 示例

以下示例配置了 **GitHub** 网站的自动登录，并包含了所有必需的选择器变量。

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
  # 基础信息
  -e SITE1_URL="https://github.com/login" \
  -e SITE1_USER="YOUR_GITHUB_USERNAME" \
  -e SITE1_PASS="YOUR_GITHUB_PASSWORD" \
  -e SITE1_CRON="5 3 * * *" \
  # 登录流程配置 (CSS Selectors)
  -e SITE1_USER_SELECTOR="#login_field" \
  -e SITE1_PASS_SELECTOR="#password" \
  -e SITE1_SUBMIT_SELECTOR="input[name='commit']" \
  -e SITE1_VERIFY_SELECTOR="img.avatar.circle" \
  \
  # --- 你可以继续添加 SITE2, SITE3 ... ---
  # -e SITE2_URL="..." \
  # -e SITE2_USER="..." \
  # ... 等等
  \
  # --- 指定要运行的 Docker 镜像 ---
  your-dockerhub-username/your-repo-name:latest
```

### ❗ 局限性

这个通用配置方案可以覆盖绝大多数采用标准表单登录的网站。但对于以下复杂情况，可能仍然需要修改 `src/main.py` 代码：
- 需要处理 **iFrame** 内的登录表单。
- 登录流程包含多个步骤（例如，输入用户名后需要点击“下一步”才出现密码框）。
- 存在复杂的 **CAPTCHA** 人机验证。
- 登录按钮在输入账号密码前是禁用的。
---

当然。查找登录/提交按钮的 CSS 选择器是一个非常常见的任务，这里为你提供一个详细的、分步的图文指南，包含**简单方法**和**进阶方法**。

我们将以 **GitHub 的登录页面** (`https://github.com/login`) 作为实战示例。

### 工具准备

你唯一需要的工具就是你的网页浏览器（推荐 Chrome, Firefox, 或 Edge）及其内置的**开发者工具**。

- **打开开发者工具的快捷键**: 在页面上按 `F12` 键，或者右键点击页面任意位置，选择 “检查” (Inspect)。

---

### 方法一：直接复制选择器 (最简单快捷)

这个方法适用于大多数情况，可以快速得到一个可用的选择器。

#### 步骤 1: 打开目标网页和开发者工具

访问你要自动登录的网站，并按 `F12` 打开开发者工具。

#### 步骤 2: 启动元素选择器

在开发者工具的左上角，找到并点击一个看起来像 **“箭头指向方框”** 的图标。这个工具可以让你在页面上选择元素。



#### 步骤 3: 在页面上点击登录按钮

激活元素选择器后，将鼠标移动到登录按钮上，它会被高亮显示。**直接点击这个登录按钮**。



点击后，开发者工具的 “元素 (Elements)” 面板会自动跳转并高亮显示该按钮对应的 HTML 代码。

#### 步骤 4: 复制 CSS 选择器

在下方高亮的 HTML 代码行上**右键点击**，在弹出的菜单中选择 `复制 (Copy)` -> `复制选择器 (Copy selector)`。



现在，这个按钮的 CSS 选择器已经被复制到你的剪贴板里了！它可能看起来像这样：
`#login > div.auth-form-body.mt-3 > form > div > input.btn.btn-primary.btn-block.js-sign-in-button`

#### 步骤 5: (强烈推荐) 验证选择器

在将这个选择器填入环境变量之前，最好先验证一下它是否能准确地定位到且**仅**定位到这一个按钮。

1.  切换到开发者工具的 **“控制台 (Console)”** 标签页。
2.  输入 `document.querySelectorAll('你的选择器')`，然后按回车。把 `'你的选择器'` 替换成你刚刚复制的内容。
3.  **检查结果**:
    *   **理想结果**: 如果返回一个包含 1 个元素的列表 ( `NodeList [input]` )，说明选择器是完美的，它准确且唯一地找到了那个按钮。
    *   **错误结果**: 如果返回 `NodeList []` (空列表)，说明选择器是错的，没有找到任何元素。
    *   **警惕结果**: 如果返回的列表包含超过 1 个元素，说明这个选择器不够精确，它匹配了页面上的多个元素，可能会点错按钮。



---

### 方法二：手动编写更稳定、更简洁的选择器 (进阶推荐)

有时自动复制的选择器过于复杂和脆弱（例如，它依赖于 HTML 的层级结构，一旦前端稍作修改就可能失效）。手动编写一个更具语义化的选择器会更加稳定。

同样，先通过方法一的步骤 1-3 定位到按钮的 HTML 代码。这次我们不直接复制，而是**分析它的属性**。

以 GitHub 的登录按钮为例，它的 HTML 如下：
```html
<input type="submit" name="commit" value="Sign in" class="btn btn-primary btn-block js-sign-in-button" data-disable-with="Signing in…" data-signin-label="Sign in" data-sso-label="Sign in with SSO" development="false">
```

我们可以寻找最能代表这个按钮的**唯一属性**。以下是编写选择器的优先顺序：

1.  **`id` 属性 (最佳)**: 如果元素有 `id`，这是最好的选择，因为 `id` 在整个页面中必须是唯一的。
    -   HTML: `<button id="login-submit-btn">登录</button>`
    -   选择器: `#login-submit-btn`

2.  **`name` 属性或唯一的 `class`**: 如果没有 `id`，一个具有描述性的 `name` 属性或一个独特的 `class` 名称也非常好。
    -   GitHub 按钮有 `name="commit"`。这看起来很独特。
    -   选择器: `input[name='commit']` (这是**属性选择器**，非常强大！)

3.  **其他属性 (如 `type`, `data-testid`)**:
    -   GitHub 按钮有 `type="submit"`。
    -   选择器: `input[type='submit']` (注意：如果页面上有多个 `type="submit"` 的按钮，这个就不够精确了)
    -   现代 web 应用经常使用 `data-testid` 或 `data-cy` 等属性用于自动化测试，这些是极好的选择器目标。
    -   HTML: `<button data-testid="login-button">登录</button>`
    -   选择器: `button[data-testid='login-button']`

4.  **组合选择器**: 你可以组合标签名、类名和属性来增加唯一性。
    -   选择器: `input.btn.btn-primary[name='commit']` (选择一个同时拥有这些 class 和 name 属性的 input 标签)

#### GitHub 示例的最佳选择

对于 GitHub 登录按钮，`input[name='commit']` 是一个非常棒的选择。它比自动生成的长选择器更简洁，也更不容易因为页面布局变化而失效。

我们同样可以在控制台验证它：`document.querySelectorAll("input[name='commit']")`，你会发现它同样准确地找到了那一个按钮。

### 总结

| 场景 | 推荐方法 | 步骤 |
| :--- | :--- | :--- |
| **快速尝试** | **直接复制** | `右键` -> `复制` -> `复制选择器` -> `在控制台验证` |
| **追求稳定性和长期维护** | **手动编写** | `检查元素HTML` -> `寻找id, name, 或特殊属性` -> `编写简洁的选择器` -> `在控制台验证` |

对于你的项目，将找到并验证过的**最佳选择器**（例如 `"input[name='commit']"`）填入 `SITE{i}_SUBMIT_SELECTOR` 环境变量中，你的自动化机器人就会变得非常稳定可靠。


## 📄 License

本项目采用 [MIT License](LICENSE) 开源。
