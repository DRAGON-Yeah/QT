# 菜单结构迁移指南

## 概述

本文档描述了从旧的平级菜单结构迁移到新的二级菜单结构的详细步骤和注意事项。

## 迁移前准备

### 1. 备份现有数据
```bash
# 备份菜单数据
python manage.py dumpdata core.Menu > backup/menu_backup_$(date +%Y%m%d).json

# 备份用户菜单配置
python manage.py dumpdata core.UserMenuConfig > backup/user_menu_config_backup_$(date +%Y%m%d).json

# 备份数据库
pg_dump quanttrade > backup/database_backup_$(date +%Y%m%d).sql
```

### 2. 检查依赖关系
```bash
# 检查菜单相关的权限配置
python manage.py shell -c "
from apps.core.models import Menu
from django.contrib.auth.models import Permission
print('现有菜单数量:', Menu.objects.count())
print('相关权限数量:', Permission.objects.filter(content_type__app_label='core').count())
"
```

## 迁移步骤

### 第一步：更新后端代码

#### 1. 更新菜单初始化命令
新的菜单结构已在 `backend/apps/core/management/commands/init_menus.py` 中定义。

#### 2. 运行菜单迁移
```bash
# 进入后端目录
cd backend

# 激活虚拟环境
source .venv/bin/activate

# 运行新的菜单初始化
python manage.py init_menus --tenant-name=default

# 验证菜单结构
python manage.py shell -c "
from apps.core.models import Menu
print('新菜单总数:', Menu.objects.count())
print('一级菜单数:', Menu.objects.filter(parent__isnull=True).count())
print('二级菜单数:', Menu.objects.filter(parent__isnull=False).count())
"
```