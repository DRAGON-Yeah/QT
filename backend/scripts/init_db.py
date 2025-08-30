#!/usr/bin/env python
"""
数据库初始化脚本
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# 初始化Django
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import Tenant, Role, Permission

User = get_user_model()


def create_superuser():
    """创建超级用户"""
    if not User.objects.filter(is_superuser=True).exists():
        print("创建超级用户...")
        User.objects.create_superuser(
            username='admin',
            email='admin@quanttrade.com',
            password='admin123'
        )
        print("超级用户创建完成: admin/admin123")
    else:
        print("超级用户已存在")


def create_default_tenant():
    """创建默认租户"""
    tenant, created = Tenant.objects.get_or_create(
        name='默认租户',
        defaults={
            'description': '系统默认租户',
            'is_active': True
        }
    )
    if created:
        print(f"创建默认租户: {tenant.name}")
    else:
        print(f"默认租户已存在: {tenant.name}")
    return tenant


def create_default_roles():
    """创建默认角色"""
    roles_data = [
        {
            'name': '系统管理员',
            'code': 'admin',
            'description': '系统管理员，拥有所有权限'
        },
        {
            'name': '交易员',
            'code': 'trader',
            'description': '交易员，可以进行交易操作'
        },
        {
            'name': '观察者',
            'code': 'viewer',
            'description': '观察者，只能查看数据'
        }
    ]
    
    for role_data in roles_data:
        role, created = Role.objects.get_or_create(
            code=role_data['code'],
            defaults=role_data
        )
        if created:
            print(f"创建角色: {role.name}")
        else:
            print(f"角色已存在: {role.name}")


def main():
    """主函数"""
    print("开始初始化数据库...")
    
    # 执行数据库迁移
    print("执行数据库迁移...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # 创建默认数据
    create_default_tenant()
    create_default_roles()
    create_superuser()
    
    print("数据库初始化完成！")


if __name__ == '__main__':
    main()