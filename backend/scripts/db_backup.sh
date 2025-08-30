#!/bin/bash
# 数据库备份脚本

set -e

# 配置
BACKUP_DIR="/app/backups"
DB_NAME="${DB_NAME:-quanttrade}"
DB_USER="${DB_USER:-quanttrade}"
DB_HOST="${DB_HOST:-localhost}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "开始备份数据库: $DB_NAME"

# PostgreSQL备份
if command -v pg_dump &> /dev/null; then
    echo "使用pg_dump备份PostgreSQL数据库..."
    pg_dump -h $DB_HOST -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/backup_${TIMESTAMP}.sql.gz
    echo "备份完成: backup_${TIMESTAMP}.sql.gz"
fi

# SQLite备份
if [ -f "/app/db.sqlite3" ]; then
    echo "备份SQLite数据库..."
    cp /app/db.sqlite3 $BACKUP_DIR/db_backup_${TIMESTAMP}.sqlite3
    echo "备份完成: db_backup_${TIMESTAMP}.sqlite3"
fi

# 清理7天前的备份
echo "清理旧备份文件..."
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete
find $BACKUP_DIR -name "db_backup_*.sqlite3" -mtime +7 -delete

echo "数据库备份完成！"