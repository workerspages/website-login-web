#!/usr/bin/env python3
import os
from sites_config import get_all_site_configs, generate_crontab_lines

def main():
    configs = get_all_site_configs()
    if not configs:
        print("无有效站点配置，退出")
        return

    lines = generate_crontab_lines(configs)
    crontab_content = '\n'.join(lines)
    
    # 写入临时Crontab文件
    with open('/tmp/crontab', 'w') as f:
        f.write(crontab_content)
    
    # 加载到Cron
    os.system('crontab /tmp/crontab')
    print(f"已加载 {len(configs)} 个站点Crontab任务")

if __name__ == '__main__':
    main()
