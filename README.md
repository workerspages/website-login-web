# Web Auto-Login Project

基于Playwright的Docker无头浏览器项目，定时自动登录多个网站，支持环境变量自定义Crontab和选择器。

## 快速启动
1. 克隆仓库：`git clone https://github.com/your-username/web-login`
2. 构建：`docker build -t web-login .`
3. 运行（示例一站点）：`docker run -d -e TZ=Asia/Shanghai -e SITE1_URL=... -e SITE1_CRONTAB="0 */6 * * *" web-login`

## 环境变量


以下是该自动登录多网站Playwright定时任务Docker项目支持的所有可配置环境变量。每个站点用不同数字编号（SITE1_、SITE2_等），均为环境变量注入，只需在Zeabur、Docker或GitHub Actions中配置即可。

***

### 基本通用变量

- `TZ`  
  容器时区（例如：`Asia/Shanghai`）。建议强制设定，保证Cron触发时间符合预期。

***

### 站点环境变量（每加一个站点，只需SITE<N>_逐项填写，对应N为1、2、3 ...）

- `SITE<N>_URL`  
  登录页面URL，**必填**。

- `SITE<N>_USERNAME`  
  账号，**必填**。

- `SITE<N>_PASSWORD`  
  密码，**必填**。

- `SITE<N>_CRONTAB`  
  Cron表达式（如：“0 */6 * * *”，分钟 小时 日 月 周），**必填**。独立控制每个站点的登录定时。  

***

### 登录逻辑可选环境变量

- `SITE<N>_USER_SELECTOR`  
  用户名输入框的CSS或XPath选择器，格式如`css:#username`或`xpath://input[@name='user']`，可选。留空时自动智能查找。

- `SITE<N>_PASS_SELECTOR`  
  密码输入框选择器，结构如上，默认智能查找。

- `SITE<N>_SUBMIT_SELECTOR`  
  登录按钮选择器，可选。留空时自动查找常见button。

- `SITE<N>_LOGIN_ACTION`  
  登录提交方式，可选：`click`（默认）、`press_enter`、`form_submit`。

- `SITE<N>_WAIT_FOR`  
  登录后等待方式，默认`dom_content_loaded`。可选：`network_idle`等。

- `SITE<N>_SUCCESS_SELECTOR`  
  登录成功后页面应出现的某元素选择器。设定后优先用此判定登录成功。

- `SITE<N>_SUCCESS_URL_REGEX`  
  登录后页面URL的正则匹配（如`^https://foo.com/dashboard`）。

- `SITE<N>_EXTRA_STEPS_JSON`  
  登录额外步骤，JSON数组形式（如`[{"click":"css:#agree"},{"wait_selector":"css:.next"}]`），用于自动勾选协议、处理弹窗等。

- `SITE<N>_HEADERS_JSON`  
  附加HTTP请求头，JSON格式（如`{"User-Agent": "xxx", "Cookie": "foo=bar"}`），如伪装UA或预置Cookie。

- `SITE<N>_VIEWPORT`  
  浏览器宽高，格式如`1280x800`。默认1280x800。

- `SITE<N>_HEADLESS`  
  设为`false`可启用有头模式（调试用），默认`true`。

- `SITE<N>_TIMEOUT_MS`  
  最大操作超时时间，单位毫秒，默认`30000`。

***

### 日志与调试

- 日志文件输出到`/var/log/site<N>.log`，每个站点各自单独。
- 建议通过挂载卷或平台日志查看（调试时可加大cron频率）。

***

### 多站点配置样例

```env
TZ=Asia/Shanghai

SITE1_URL=https://example.com/login
SITE1_USERNAME=alice
SITE1_PASSWORD=secret
SITE1_CRONTAB=0 */6 * * *
SITE1_USER_SELECTOR=css:#user
SITE1_PASS_SELECTOR=xpath://input[@type="password"]
SITE1_SUBMIT_SELECTOR=css:button[type='submit']
SITE1_SUCCESS_SELECTOR=css:.profile
SITE1_SUCCESS_URL_REGEX=^https://example.com/panel

SITE2_URL=https://foo.com/sign
SITE2_USERNAME=bob
SITE2_PASSWORD=moresecret
SITE2_CRONTAB=15 2,14 * * 1-5
```

***

### 高级/容器相关变量（可选）

- `PYTHONUNBUFFERED=1`
- `SHM_SIZE=1g`（部分平台需要大共享内存，Playwright建议）
- `USE_SCHEDULER`（如脚本内自用定时，当前方案用Cron，可忽略）

***

只要将上述变量按SITE编号补齐，即可支持任意多个网站的独立参数、定时和登录逻辑。无须更改镜像和代码，全部环境变量可在部署面板动态填写。
