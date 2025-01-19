# 部署指南

## 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少2GB RAM
- 10GB可用磁盘空间

## 部署步骤

### 1. 准备环境

1. 安装Docker和Docker Compose：
```bash
# 安装Docker
curl -fsSL https://get.docker.com | sh

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. 创建必要的目录：
```bash
mkdir -p nginx/conf.d nginx/ssl logs static
```

### 2. 配置环境变量

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 修改`.env`文件，设置适当的值：
- 数据库配置
- JWT密钥
- 应用端口
- 日志级别等

### 3. SSL证书

1. 如果使用Let's Encrypt：
```bash
# 安装certbot
sudo apt-get update
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com
```

2. 复制证书到nginx目录：
```bash
sudo cp /etc/letsencrypt/live/your-domain.com/* nginx/ssl/
```

### 4. 启动服务

1. 构建镜像：
```bash
docker-compose build
```

2. 启动服务：
```bash
docker-compose up -d
```

3. 检查服务状态：
```bash
docker-compose ps
```

### 5. 数据库迁移

1. 执行数据库迁移：
```bash
docker-compose exec app poetry run alembic upgrade head
```

### 6. 验证部署

1. 检查服务健康状态：
```bash
curl http://localhost/health
```

2. 访问API文档：
```
https://your-domain.com/docs
```

## 监控和维护

### 日志查看

- 应用日志：
```bash
docker-compose logs -f app
```

- Nginx日志：
```bash
docker-compose logs -f nginx
```

### 备份

1. 数据库备份：
```bash
docker-compose exec db pg_dump -U postgres food_journey > backup.sql
```

2. 恢复数据库：
```bash
docker-compose exec -T db psql -U postgres food_journey < backup.sql
```

### 更新部署

1. 拉取最新代码：
```bash
git pull origin main
```

2. 重新构建并启动：
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

### 常见问题

1. 数据库连接失败
- 检查数据库容器是否运行
- 验证数据库配置是否正确
- 确保数据库初始化完成

2. Nginx 502错误
- 检查应用容器是否正常运行
- 查看应用日志是否有错误
- 验证upstream配置是否正确

3. SSL证书问题
- 确保证书文件存在且权限正确
- 检查nginx配置中的证书路径
- 验证证书是否过期

## 安全建议

1. 定期更新依赖包
```bash
poetry update
```

2. 启用HTTPS和HSTS
- 在nginx配置中取消HSTS注释
- 确保所有流量都通过HTTPS

3. 设置强密码策略
- 修改数据库密码
- 更新JWT密钥
- 使用安全的环境变量

4. 定期备份
- 设置自动备份脚本
- 测试备份恢复流程

5. 监控系统资源
- 使用监控工具（如Prometheus + Grafana）
- 设置告警阈值

## 性能优化

1. 数据库优化
- 添加适当的索引
- 优化查询语句
- 配置连接池

2. 缓存策略
- 使用Redis缓存热点数据
- 配置Nginx缓存
- 启用压缩

3. 负载均衡
- 配置多个应用实例
- 使用Nginx负载均衡
- 考虑使用CDN 