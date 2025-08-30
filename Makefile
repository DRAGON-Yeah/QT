# QuantTrade Makefile
# 简化Docker和开发操作的命令集合

.PHONY: help setup dev-up dev-down dev-restart dev-logs dev-shell dev-test prod-deploy prod-up prod-down prod-logs backup restore clean build health monitor

# 默认目标
help:
	@echo "QuantTrade 开发和部署命令"
	@echo ""
	@echo "开发环境:"
	@echo "  setup        - 初始化开发环境"
	@echo "  dev-up       - 启动开发环境"
	@echo "  dev-down     - 停止开发环境"
	@echo "  dev-restart  - 重启开发环境"
	@echo "  dev-logs     - 查看开发环境日志"
	@echo "  dev-shell    - 进入后端容器shell"
	@echo "  dev-test     - 运行测试"
	@echo ""
	@echo "生产环境:"
	@echo "  prod-deploy  - 部署生产环境"
	@echo "  prod-up      - 启动生产环境"
	@echo "  prod-down    - 停止生产环境"
	@echo "  prod-logs    - 查看生产环境日志"
	@echo ""
	@echo "数据管理:"
	@echo "  backup       - 备份数据库"
	@echo "  restore      - 恢复数据库"
	@echo ""
	@echo "维护操作:"
	@echo "  clean        - 清理Docker资源"
	@echo "  build        - 重新构建镜像"
	@echo "  health       - 健康检查"
	@echo "  monitor      - 系统监控"

# 初始化开发环境
setup:
	@echo "初始化QuantTrade开发环境..."
	@chmod +x scripts/*.sh
	@./scripts/docker-setup.sh
	@echo "环境初始化完成！"

# 开发环境操作
dev-up:
	@echo "启动开发环境..."
	@docker-compose up -d
	@echo "开发环境启动完成！"
	@echo "前端: http://localhost:3000"
	@echo "后端: http://localhost:8000"
	@echo "管理后台: http://localhost:8000/admin/"

dev-down:
	@echo "停止开发环境..."
	@docker-compose down

dev-restart:
	@echo "重启开发环境..."
	@docker-compose restart

dev-logs:
	@docker-compose logs -f

dev-shell:
	@docker-compose exec backend bash

dev-test:
	@echo "运行测试..."
	@docker-compose exec backend python manage.py test

# 数据库操作
migrate:
	@echo "执行数据库迁移..."
	@docker-compose exec backend python manage.py migrate

makemigrations:
	@echo "创建数据库迁移..."
	@docker-compose exec backend python manage.py makemigrations

createsuperuser:
	@echo "创建超级用户..."
	@docker-compose exec backend python manage.py createsuperuser

# 生产环境操作
prod-deploy:
	@echo "部署生产环境..."
	@./scripts/docker-prod.sh deploy

prod-up:
	@echo "启动生产环境..."
	@./scripts/docker-prod.sh start

prod-down:
	@echo "停止生产环境..."
	@./scripts/docker-prod.sh stop

prod-logs:
	@docker-compose -f docker-compose.prod.yml logs -f

# 数据管理
backup:
	@echo "备份数据库..."
	@./scripts/docker-prod.sh backup

restore:
	@echo "恢复数据库..."
	@read -p "请输入备份文件路径: " backup_file; \
	./scripts/docker-prod.sh restore $$backup_file

# 维护操作
clean:
	@echo "清理Docker资源..."
	@docker-compose down -v --remove-orphans
	@docker system prune -f
	@echo "清理完成"

build:
	@echo "重新构建镜像..."
	@docker-compose build --no-cache

build-prod:
	@echo "构建生产环境镜像..."
	@docker-compose -f docker-compose.prod.yml build --no-cache

# 监控和检查
health:
	@echo "执行健康检查..."
	@./scripts/health-check.sh

monitor:
	@echo "启动系统监控..."
	@./scripts/docker-monitor.sh monitor

stats:
	@echo "显示容器资源使用情况..."
	@./scripts/docker-monitor.sh stats

# 代码质量检查
lint:
	@echo "代码质量检查..."
	@docker-compose exec backend flake8 .
	@docker-compose exec backend black --check .

format:
	@echo "代码格式化..."
	@docker-compose exec backend black .
	@docker-compose exec backend isort .

# 安全检查
security-check:
	@echo "安全检查..."
	@docker-compose exec backend safety check
	@docker-compose exec backend bandit -r .

# 性能测试
load-test:
	@echo "性能测试..."
	@docker-compose exec backend locust -f tests/load_test.py --host=http://localhost:8000

# 文档生成
docs:
	@echo "生成API文档..."
	@docker-compose exec backend python manage.py spectacular --file schema.yml
	@echo "API文档已生成: schema.yml"

# 数据初始化
init-data:
	@echo "初始化测试数据..."
	@docker-compose exec backend python manage.py loaddata fixtures/initial_data.json

# 日志管理
logs-backend:
	@docker-compose logs -f backend

logs-frontend:
	@docker-compose logs -f frontend

logs-celery:
	@docker-compose logs -f celery

logs-db:
	@docker-compose logs -f db

logs-redis:
	@docker-compose logs -f redis

# 开发工具
shell-db:
	@docker-compose exec db psql -U quanttrade quanttrade_dev

shell-redis:
	@docker-compose exec redis redis-cli

# 更新依赖
update-deps:
	@echo "更新Python依赖..."
	@docker-compose exec backend pip-compile requirements/base.in
	@docker-compose exec backend pip-compile requirements/development.in
	@docker-compose exec backend pip-compile requirements/production.in