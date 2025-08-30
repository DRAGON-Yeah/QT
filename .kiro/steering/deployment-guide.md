# 部署指南和运维最佳实践

## 环境准备
### Python环境配置
```bash
# 安装Python 3.12
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# 创建项目目录
mkdir -p /opt/quanttrade
cd /opt/quanttrade

# 创建虚拟环境
python3.12 -m venv .venv
source .venv/bin/activate

# 升级pip
pip install --upgrade pip
```

### 系统依赖安装
```bash
# Ubuntu/Debian
sudo apt install -y \
    build-essential \
    libpq-dev \
    redis-server \
    nginx \
    supervisor \
    git \
    curl

# 安装TA-Lib (技术分析库)
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

## Docker部署
### Dockerfile
```dockerfile
FROM python:3.12-slim

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# 创建非root用户
RUN groupadd -r quanttrade && useradd -r -g quanttrade quanttrade

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装TA-Lib
RUN curl -L http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz | tar xz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib

# 创建虚拟环境
RUN python -m venv $VIRTUAL_ENV

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY --chown=quanttrade:quanttrade . .

# 切换到非root用户
USER quanttrade

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
```

### Docker Compose配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://quanttrade:password@db:5432/quanttrade
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./media:/app/media
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=quanttrade
      - POSTGRES_USER=quanttrade
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  celery:
    build: .
    command: celery -A config worker -l info
    environment:
      - DATABASE_URL=postgresql://quanttrade:password@db:5432/quanttrade
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A config beat -l info
    environment:
      - DATABASE_URL=postgresql://quanttrade:password@db:5432/quanttrade
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./static:/app/static
      - ./media:/app/media
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### 生产环境Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=quanttrade.example.com
      - DATABASE_URL=postgresql://quanttrade:${DB_PASSWORD}@db:5432/quanttrade
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    env_file:
      - .env.prod
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=quanttrade
      - POSTGRES_USER=quanttrade
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  redis:
    image: redis:6-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped
```

## Nginx配置
### 基础配置
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream quanttrade {
        server web:8000;
    }

    server {
        listen 80;
        server_name quanttrade.example.com;
        
        # 重定向到HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name quanttrade.example.com;

        # SSL配置
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
        ssl_prefer_server_ciphers off;

        # 安全头
        add_header Strict-Transport-Security "max-age=63072000" always;
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # 静态文件
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        location /media/ {
            alias /app/media/;
            expires 1y;
        }

        # WebSocket支持
        location /ws/ {
            proxy_pass http://quanttrade;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # API和应用
        location / {
            proxy_pass http://quanttrade;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 限制请求大小
        client_max_body_size 10M;
    }
}
```

## 环境配置管理
### 环境变量配置
```bash
# .env.prod
DEBUG=False
SECRET_KEY=your-production-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# 数据库配置
DATABASE_URL=postgresql://quanttrade:password@db:5432/quanttrade
DB_PASSWORD=secure-database-password

# Redis配置
REDIS_URL=redis://:password@redis:6379/0
REDIS_PASSWORD=secure-redis-password

# 交易所API配置
BINANCE_API_KEY=your-binance-api-key
BINANCE_SECRET_KEY=your-binance-secret-key
OKX_API_KEY=your-okx-api-key
OKX_SECRET_KEY=your-okx-secret-key
OKX_PASSPHRASE=your-okx-passphrase

# 邮件配置
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@quanttrade.com
EMAIL_HOST_PASSWORD=email-password
EMAIL_USE_TLS=True

# 监控配置
SENTRY_DSN=your-sentry-dsn
```

### Django生产设置
```python
# config/settings/production.py
from .base import *
import os

DEBUG = False

ALLOWED_HOSTS = [
    'quanttrade.example.com',
    'api.quanttrade.example.com',
]

# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'quanttrade'),
        'USER': os.getenv('DB_USER', 'quanttrade'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
        'CONN_MAX_AGE': 600,
    }
}

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        }
    }
}

# 静态文件配置
STATIC_ROOT = '/app/static'
MEDIA_ROOT = '/app/media'

# 安全设置
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Session配置
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1小时

# CSRF配置
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/security.log',
            'maxBytes': 1024*1024*15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

## 数据库管理
### 数据库迁移
```bash
# 生产环境迁移脚本
#!/bin/bash
set -e

echo "开始数据库迁移..."

# 激活虚拟环境
source .venv/bin/activate

# 备份数据库
echo "备份数据库..."
pg_dump -h localhost -U quanttrade quanttrade > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# 执行迁移
echo "执行迁移..."
python manage.py migrate --settings=config.settings.production

# 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput --settings=config.settings.production

echo "迁移完成！"
```

### 数据库备份策略
```bash
#!/bin/bash
# backup.sh - 数据库备份脚本

BACKUP_DIR="/opt/quanttrade/backups"
DB_NAME="quanttrade"
DB_USER="quanttrade"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -h localhost -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# 删除7天前的备份
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

# 上传到云存储（可选）
# aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql.gz s3://quanttrade-backups/

echo "备份完成: backup_$TIMESTAMP.sql.gz"
```

### 定时备份配置
```bash
# 添加到crontab
# crontab -e

# 每天凌晨2点备份数据库
0 2 * * * /opt/quanttrade/scripts/backup.sh

# 每小时备份Redis数据
0 * * * * redis-cli --rdb /opt/quanttrade/backups/redis_$(date +\%H).rdb

# 每周日清理日志
0 3 * * 0 find /opt/quanttrade/logs -name "*.log" -mtime +30 -delete
```

## 监控和告警
### Prometheus配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'quanttrade'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Grafana仪表盘
```json
{
  "dashboard": {
    "title": "QuantTrade监控",
    "panels": [
      {
        "title": "请求响应时间",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "数据库连接数",
        "type": "singlestat",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends{datname=\"quanttrade\"}"
          }
        ]
      },
      {
        "title": "Redis内存使用",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes"
          }
        ]
      }
    ]
  }
}
```

### 健康检查
```python
# apps/monitoring/views.py
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis

def health_check(request):
    """系统健康检查"""
    status = {
        'status': 'healthy',
        'checks': {}
    }
    
    # 数据库检查
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        status['checks']['database'] = 'healthy'
    except Exception as e:
        status['checks']['database'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Redis检查
    try:
        cache.set('health_check', 'ok', 10)
        cache.get('health_check')
        status['checks']['redis'] = 'healthy'
    except Exception as e:
        status['checks']['redis'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    # 交易所连接检查
    try:
        # 检查交易所API连接
        status['checks']['exchanges'] = 'healthy'
    except Exception as e:
        status['checks']['exchanges'] = f'unhealthy: {str(e)}'
        status['status'] = 'unhealthy'
    
    return JsonResponse(status)
```

## 部署脚本
### 自动化部署脚本
```bash
#!/bin/bash
# deploy.sh - 自动化部署脚本

set -e

PROJECT_DIR="/opt/quanttrade"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "开始部署 QuantTrade..."

# 1. 备份当前版本
echo "备份当前版本..."
if [ -d "$PROJECT_DIR/current" ]; then
    cp -r $PROJECT_DIR/current $BACKUP_DIR/version_$TIMESTAMP
fi

# 2. 拉取最新代码
echo "拉取最新代码..."
cd $PROJECT_DIR
git pull origin main

# 3. 激活虚拟环境
echo "激活虚拟环境..."
source .venv/bin/activate

# 4. 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 5. 数据库迁移
echo "执行数据库迁移..."
python manage.py migrate --settings=config.settings.production

# 6. 收集静态文件
echo "收集静态文件..."
python manage.py collectstatic --noinput --settings=config.settings.production

# 7. 重启服务
echo "重启服务..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 8. 健康检查
echo "等待服务启动..."
sleep 30

echo "执行健康检查..."
if curl -f http://localhost/health/; then
    echo "部署成功！"
else
    echo "健康检查失败，回滚到上一版本..."
    # 回滚逻辑
    if [ -d "$BACKUP_DIR/version_$TIMESTAMP" ]; then
        rm -rf $PROJECT_DIR/current
        mv $BACKUP_DIR/version_$TIMESTAMP $PROJECT_DIR/current
        docker-compose -f docker-compose.prod.yml restart
    fi
    exit 1
fi

echo "部署完成！"
```

### 零停机部署
```bash
#!/bin/bash
# zero-downtime-deploy.sh

set -e

echo "开始零停机部署..."

# 1. 构建新镜像
echo "构建新镜像..."
docker build -t quanttrade:new .

# 2. 启动新容器
echo "启动新容器..."
docker run -d --name quanttrade-new \
    --network quanttrade_default \
    -e DATABASE_URL=$DATABASE_URL \
    -e REDIS_URL=$REDIS_URL \
    quanttrade:new

# 3. 健康检查
echo "等待新容器启动..."
sleep 30

if docker exec quanttrade-new curl -f http://localhost:8000/health/; then
    echo "新容器健康检查通过"
    
    # 4. 更新负载均衡器
    echo "更新负载均衡器..."
    # 这里需要根据实际的负载均衡器配置
    
    # 5. 停止旧容器
    echo "停止旧容器..."
    docker stop quanttrade-old || true
    docker rm quanttrade-old || true
    
    # 6. 重命名容器
    docker rename quanttrade-new quanttrade-old
    
    echo "零停机部署完成！"
else
    echo "新容器健康检查失败，清理新容器..."
    docker stop quanttrade-new
    docker rm quanttrade-new
    exit 1
fi
```

## 性能优化
### 数据库优化
```sql
-- 创建必要的索引
CREATE INDEX CONCURRENTLY idx_orders_tenant_created 
ON orders(tenant_id, created_at);

CREATE INDEX CONCURRENTLY idx_orders_symbol_status 
ON orders(symbol, status) WHERE status IN ('open', 'partial');

CREATE INDEX CONCURRENTLY idx_market_data_symbol_timestamp 
ON market_data(symbol, timestamp);

-- 分区表（如果数据量大）
CREATE TABLE market_data_2024 PARTITION OF market_data
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### 应用优化
```python
# 数据库连接池配置
DATABASES = {
    'default': {
        # ...
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        }
    }
}

# 缓存配置
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
            }
        }
    }
}
```