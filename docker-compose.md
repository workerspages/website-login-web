以下是一个完整的、可直接使用的 docker-compose.yml 示例，适用于常见的多服务场景，包括一个网站登录核心应用、数据库，以及一个备份/同步组件。你可以直接复制到项目中使用，必要时替换镜像名、端口、卷路径和环境变量即可。

完整示例

```yaml
version: "3.9"

services:
  app:
    image: your-registry/website-login:latest
    container_name: website-login
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "8080:8080"      # 根据实际应用端口调整
    environment:
      - TZ=${TZ:-Asia/Shanghai}
      - APP_ENV=${APP_ENV:-production}
      - SITE1_URL=${SITE1_URL}
      - SITE1_USERNAME=${SITE1_USERNAME}
      - SITE1_PASSWORD=${SITE1_PASSWORD}
      - SITE1_USER_SELECTOR=${SITE1_USER_SELECTOR}
      - SITE1_PASS_SELECTOR=${SITE1_PASS_SELECTOR}
      - SITE1_SUBMIT_SELECTOR=${SITE1_SUBMIT_SELECTOR}
      - SITE1_SUCCESS_SELECTOR=${SITE1_SUCCESS_SELECTOR}
      - SITE1_SUCCESS_URL_REGEX=${SITE1_SUCCESS_URL_REGEX}
      - SITE1_CRONTAB=${SITE1_CRONTAB}
      - SITE2_URL=${SITE2_URL}
      - SITE2_USERNAME=${SITE2_USERNAME}
      - SITE2_PASSWORD=${SITE2_PASSWORD}
      - SITE2_USER_SELECTOR=${SITE2_USER_SELECTOR}
      - SITE2_PASS_SELECTOR=${SITE2_PASS_SELECTOR}
      - SITE2_SUBMIT_SELECTOR=${SITE2_SUBMIT_SELECTOR}
      - SITE2_SUCCESS_SELECTOR=${SITE2_SUCCESS_SELECTOR}
      - SITE2_SUCCESS_URL_REGEX=${SITE2_SUCCESS_URL_REGEX}
      - SITE2_CRONTAB=${SITE2_CRONTAB}
    volumes:
      - web_data:/data
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  db:
    image: postgres:13
    container_name: website-login-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${DB_USER:-dbuser}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-dbpass}
      - POSTGRES_DB=${DB_NAME:-website_login}
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "dbuser"]
      interval: 30s
      timeout: 10s
      retries: 5

  backup:
    image: your-registry/duplicati:latest
    container_name: backup-duplicati
    restart: unless-stopped
    depends_on:
      - app
    environment:
      - DAV_TARGET=${DAV_TARGET}
      - DAV_USERNAME=${DAV_USERNAME}
      - DAV_PASSWORD=${DAV_PASSWORD}
      - BACKUP_SCHEDULE=${BACKUP_SCHEDULE:-0 */12 * * *}
    volumes:
      - backup_data:/backups
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "8300:8300"      # Web UI 端口，如不需要可删掉
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  web_data:
  db_data:
  backup_data:

networks:
  default:
    driver: bridge
```

环境变量示例
```
- TZ: Asia/Shanghai
- APP_ENV: production
- SITE1_URL, SITE1_USERNAME, SITE1_PASSWORD: 第一个站点的登录信息
- SITE1_USER_SELECTOR, SITE1_PASS_SELECTOR, SITE1_SUBMIT_SELECTOR: 登录字段选择器（可选，若不提供将启用智能定位）
- SITE1_SCHEDULE: 如 cron 表达式，用于定时执行（如果你把调度放在应用端，不走容器级计划，可忽略）
- SITE1_SUCCESS_SELECTOR: 登录成功后出现的元素选择器
- SITE1_SUCCESS_URL_REGEX: 登录成功后的 URL 正则
- SITE2_URL, SITE2_USERNAME, SITE2_PASSWORD, SITE2_USER_SELECTOR, SITE2_PASS_SELECTOR, SITE2_SUBMIT_SELECTOR, SITE2_SUCCESS_SELECTOR, SITE2_SUCCESS_URL_REGEX, SITE2_CRONTAB: 第二个站点的同等设置
- DAV_TARGET, DAV_USERNAME, DAV_PASSWORD: WebDAV 备份目标的凭证
```

注意事项
- 替换镜像路径为实际私有镜像库中的镜像名，确保镜像存在且可访问。
- 数据库端口公开到宿主机可能带来安全风险，如不需要外部访问，移除 ports 映射，改为内部网络访问。
- 如果需要使用 Docker Secrets 来管理敏感信息，可以将 environment 部分替换为 secrets 的引用，提升安全性。
- 如果你使用的备份工具镜像名称、端口或健康检查不同，请按实际情况调整 backup 服务的配置。

如果需要，我可以根据你的具体镜像、端口、数据库、备份目标等进一步定制一份完全匹配你环境的 docker-compose.yml，并附上逐步部署和测试方案。请提供你实际使用的镜像名称、端口、需要暴露的服务、以及备份目标类型等信息。
