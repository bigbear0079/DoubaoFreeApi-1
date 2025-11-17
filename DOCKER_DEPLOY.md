# Docker 部署指南

## 📦 快速开始

### 1. 前置要求

确保你的 Ubuntu Server 已安装：
- Docker
- Docker Compose

如果未安装，运行：
```bash
# 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 安装 Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

### 2. 克隆项目

```bash
git clone https://github.com/bigbear0079/DoubaoFreeApi-1.git
cd DoubaoFreeApi-1
```

### 3. 配置 Session

在项目根目录创建 `session.json` 文件：

```json
{
  "guest_sessions": [],
  "user_sessions": []
}
```

或者运行自动获取脚本：
```bash
python auto_get_session.py
```

### 4. 构建并启动

```bash
# 构建镜像并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 5. 访问服务

服务启动后，访问：
- API 文档: http://your-server-ip:8000/docs
- 主页: http://your-server-ip:8000

## 🔧 常用命令

```bash
# 查看运行状态
docker-compose ps

# 查看实时日志
docker-compose logs -f doubao-api

# 重启服务
docker-compose restart

# 停止服务
docker-compose stop

# 启动服务
docker-compose start

# 完全删除容器和网络
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 更新代码后重启
git pull
docker-compose up -d --build
```

## 📝 配置说明

### 端口映射

默认映射 `8000:8000`，如需修改，编辑 `docker-compose.yml`：

```yaml
ports:
  - "9000:8000"  # 将宿主机 9000 端口映射到容器 8000 端口
```

### 数据持久化

以下文件会自动挂载到宿主机，重启容器不会丢失：
- `session.json` - Session 数据
- `video_links.json` - 视频任务数据

### 开发模式

如需实时更新代码（不重启容器），取消 `docker-compose.yml` 中的注释：

```yaml
volumes:
  - ./src:/app/src
  - ./app.py:/app/app.py
```

## 🔒 安全建议

### 1. 使用反向代理

推荐使用 Nginx 作为反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 配置 HTTPS

使用 Let's Encrypt 免费证书：

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 3. 限制访问

在 `docker-compose.yml` 中只绑定本地：

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

## 🐛 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker-compose logs doubao-api

# 检查端口占用
sudo netstat -tulpn | grep 8000

# 检查 Docker 状态
sudo systemctl status docker
```

### Session 失效

```bash
# 进入容器
docker-compose exec doubao-api bash

# 运行 Session 获取脚本
python auto_get_session.py

# 退出容器
exit

# 重启服务
docker-compose restart
```

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build
```

## 📊 监控

### 查看资源使用

```bash
# 查看容器资源使用情况
docker stats doubao-free-api
```

### 查看日志

```bash
# 实时日志
docker-compose logs -f

# 最近 100 行日志
docker-compose logs --tail=100

# 特定时间的日志
docker-compose logs --since 2024-01-01T00:00:00
```

## 🚀 性能优化

### 1. 限制资源使用

在 `docker-compose.yml` 中添加：

```yaml
services:
  doubao-api:
    # ... 其他配置
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 2. 使用生产级 WSGI 服务器

修改 `Dockerfile` 的启动命令：

```dockerfile
# 安装 gunicorn
RUN pip install gunicorn

# 使用 gunicorn 启动
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

## 📦 备份与恢复

### 备份数据

```bash
# 备份 session 和视频数据
tar -czf backup-$(date +%Y%m%d).tar.gz session.json video_links.json
```

### 恢复数据

```bash
# 解压备份
tar -xzf backup-20240101.tar.gz

# 重启服务
docker-compose restart
```

## 🔄 自动更新

创建自动更新脚本 `update.sh`：

```bash
#!/bin/bash
cd /path/to/DoubaoFreeApi-1
git pull
docker-compose up -d --build
docker image prune -f
```

添加到 crontab（每天凌晨 3 点更新）：

```bash
crontab -e
# 添加：
0 3 * * * /path/to/update.sh >> /var/log/doubao-update.log 2>&1
```

## 💡 提示

1. 首次启动可能需要几分钟来构建镜像
2. 确保 `session.json` 文件存在且格式正确
3. 定期备份 `session.json` 和 `video_links.json`
4. 生产环境建议使用反向代理和 HTTPS
5. 监控日志以及时发现问题
