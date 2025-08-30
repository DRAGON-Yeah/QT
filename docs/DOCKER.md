# QuantTrade Docker 部署指南

## 概述

QuantTrade 使用 Docker 和 Docker Compose 进行容器化部署，支持开发环境和生产环境的完整配置。

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 4GB 内存
- 至少 20GB 磁盘空间

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd quanttrade

# 初始化环境
make setup
```

### 2. 开发环境

```bash
# 启动开发环境
make dev-up

# 执行数据库迁移
make migrate

# 创建超级用户
make createsuperuser

# 查看日志
make dev-logs
```

访问地址：
- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- 管理后台：http://localhost:8000/admin/

### 3. 生产环境

```bash
# 配置生产环境变量
cp .env.prod.example .env.prod
# 编辑 .env.prod 文件，填入实际配置

# 部署生产环境
make prod-deploy
```

## 服务架构

### 开发环境服务

| 服务 | 端口 | 描述 |
|------|------|------|
| frontend | 3000 | React 前端开发服务器 |
| backend | 8000 | Django 后端 API 服务 |
| db | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存和消息队列 |
| celery | - | Celery 异步任务处理器 |
| celery-beat | - | Celery 定时任务调度器 |

### 生产环境服务

| 服务 | 端口 | 描述 |
|------|------|------|
| nginx | 80/443 | Nginx 反向代理和静态文件服务 |
| backend | - | Django 后端 API 服务（内部） |
| frontend | - | React 前端构建文件（静态） |
| db | - | PostgreSQL 数据库（内部） |
| redis | - | Redis 缓存和消息队列（内部） |
| celery | - | Celery 异步任务处理器 |
| celery-beat | - | Celery 定时任务调度器 |

## 配置文件说明

### Docker Compose 文件

- `docker-compose.yml` - 开发环境配置
- `docker-compose.prod.yml` - 生产环境配置
- `docker-compose.override.yml` - 本地开发覆盖配置

### Dockerfile 文件

- `backend/Dockerfile.dev` - 后端开发环境镜像
- `backend/Dockerfile.prod` - 后端生产环境镜像
- `frontend/Dockerfile.dev` - 前端开发环境镜像
- `frontend/Dockerfile.prod` - 前端生产环境镜像

### 环境变量文件

- `.env.example` - 环境变量示例文件
- `.env.prod.example` - 生产环境变量示例文件

## 常用命令

### 开发环境命令

```bash
# 启动服务
make dev-up

# 停止服务
make dev-down

# 重启服务
make dev-restart

# 查看日志
make dev-logs

# 进入后端容器
make dev-shell

# 运行测试
make dev-test

# 数据库迁移
make migrate

# 创建迁移文件
make makemigrations

# 创建超级用户
make createsuperuser
```

### 生产环境命令

```bash
# 部署生产环境
make prod-deploy

# 启动生产环境
make prod-up

# 停止生产环境
make prod-down

# 查看生产环境日志
make prod-logs

# 备份数据库
make backup

# 恢复数据库
make restore
```

### 维护命令

```bash
# 健康检查
make health

# 系统监控
make monitor

# 显示资源使用情况
make stats

# 清理Docker资源
make clean

# 重新构建镜像
make build

# 代码格式化
make format

# 代码质量检查
make lint

# 安全检查
make security-check
```

## 数据持久化

### 数据卷

- `postgres_data` - PostgreSQL 数据
- `redis_data` - Redis 数据
- `backend_media` - 后端媒体文件
- `backend_static` - 后端静态文件

### 备份策略

```bash
# 自动备份（生产环境）
# 每天凌晨2点自动备份数据库
0 2 * * * /opt/quanttrade/scripts/docker-prod.sh backup

# 手动备份
make backup

# 恢复备份
make restore
```

## 网络配置

### 开发环境网络

- 网络名称：`quanttrade_network`
- 类型：bridge
- 服务间通信：通过服务名称

### 生产环境网络

- 网络名称：`quanttrade_prod_network`
- 类型：bridge
- 外部访问：通过 Nginx 反向代理

## 安全配置

### SSL/TLS 配置

```bash
# 生成自签名证书（开发环境）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem

# 生产环境建议使用 Let's Encrypt
certbot certonly --webroot -w /var/www/html -d quanttrade.example.com
```

### 环境变量安全

- 使用强密码
- 定期轮换密钥
- 不要在代码中硬编码敏感信息
- 使用 Docker secrets（生产环境）

## 监控和日志

### 日志管理

```bash
# 查看特定服务日志
make logs-backend
make logs-frontend
make logs-celery
make logs-db
make logs-redis

# 实时监控
make monitor

# 健康检查
make health
```

### 性能监控

```bash
# 显示容器资源使用情况
make stats

# 性能测试
make load-test
```

## 故障排除

### 常见问题

1. **端口冲突**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8000
   
   # 修改端口配置
   # 编辑 docker-compose.yml 中的端口映射
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   make shell-db
   
   # 重启数据库服务
   docker-compose restart db
   ```

3. **Redis连接失败**
   ```bash
   # 检查Redis状态
   make shell-redis
   
   # 重启Redis服务
   docker-compose restart redis
   ```

4. **Celery任务不执行**
   ```bash
   # 检查Celery状态
   docker-compose exec celery celery -A config inspect ping
   
   # 重启Celery服务
   docker-compose restart celery
   ```

### 调试技巧

```bash
# 进入容器调试
docker-compose exec backend bash
docker-compose exec frontend sh

# 查看容器详细信息
docker-compose ps
docker inspect <container_name>

# 查看网络连接
docker network ls
docker network inspect quanttrade_network
```

## 性能优化

### 资源限制

```yaml
# 在 docker-compose.prod.yml 中设置资源限制
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 缓存优化

- 使用多阶段构建减少镜像大小
- 合理配置 Redis 缓存策略
- 启用 Nginx 静态文件缓存

### 数据库优化

- 配置连接池
- 定期执行 VACUUM 和 ANALYZE
- 监控慢查询日志

## 扩展部署

### 水平扩展

```bash
# 扩展后端服务
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# 扩展Celery Worker
docker-compose -f docker-compose.prod.yml up -d --scale celery=5
```

### 负载均衡

- 使用 Nginx upstream 配置负载均衡
- 配置健康检查
- 实现会话粘性（如需要）

## 更新和维护

### 应用更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
make build

# 滚动更新
docker-compose up -d --no-deps backend
```

### 系统维护

```bash
# 清理旧镜像
docker image prune -f

# 清理未使用的数据卷
docker volume prune -f

# 系统资源清理
make clean
```

## 最佳实践

1. **开发环境**
   - 使用数据卷挂载源代码，支持热重载
   - 启用调试模式和详细日志
   - 使用测试数据库

2. **生产环境**
   - 使用多阶段构建优化镜像大小
   - 配置健康检查和重启策略
   - 实施资源限制和监控
   - 定期备份数据

3. **安全**
   - 使用非root用户运行容器
   - 定期更新基础镜像
   - 扫描镜像安全漏洞
   - 配置防火墙规则

4. **监控**
   - 配置日志聚合
   - 实施应用性能监控
   - 设置告警规则
   - 定期健康检查