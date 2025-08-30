# -*- coding: utf-8 -*-
"""
菜单管理服务
"""
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from typing import List, Dict, Any, Optional
import json

from .models import Menu, UserMenuConfig, MenuPermissionCache
from ..users.models import User


class MenuService:
    """菜单服务类"""
    
    CACHE_TIMEOUT = 3600  # 缓存1小时
    
    @classmethod
    def get_user_menus(cls, user: User, use_cache: bool = True) -> List[Dict[str, Any]]:
        """获取用户可访问的菜单树"""
        cache_key = f"user_menus_{user.tenant.id}_{user.id}"
        
        if use_cache:
            cached_menus = cache.get(cache_key)
            if cached_menus:
                return cached_menus
        
        # 获取用户权限
        user_permissions = cls._get_user_permissions(user)
        
        # 获取所有可见菜单
        menus = Menu.objects.filter(
            tenant=user.tenant,
            is_visible=True,
            is_enabled=True
        ).select_related('parent').prefetch_related('permissions', 'roles')
        
        # 过滤权限
        accessible_menus = []
        for menu in menus:
            if cls._check_menu_permission(menu, user, user_permissions):
                accessible_menus.append(menu)
        
        # 构建菜单树
        menu_tree = cls._build_menu_tree(accessible_menus, user)
        
        # 缓存结果
        if use_cache:
            cache.set(cache_key, menu_tree, cls.CACHE_TIMEOUT)
        
        return menu_tree
    
    @classmethod
    def _get_user_permissions(cls, user: User) -> set:
        """获取用户所有权限"""
        permissions = set()
        
        # 用户直接权限
        permissions.update(user.user_permissions.values_list('codename', flat=True))
        
        # 角色权限
        for role in user.roles.all():
            permissions.update(role.permissions.values_list('codename', flat=True))
        
        return permissions
    
    @classmethod
    def _check_menu_permission(cls, menu: Menu, user: User, user_permissions: set) -> bool:
        """检查菜单权限"""
        # 超级管理员可以访问所有菜单
        if user.is_superuser:
            return True
        
        # 检查角色权限
        if menu.roles.exists():
            user_roles = set(user.roles.values_list('id', flat=True))
            menu_roles = set(menu.roles.values_list('id', flat=True))
            if not user_roles.intersection(menu_roles):
                return False
        
        # 检查具体权限
        if menu.permissions.exists():
            menu_permissions = set(menu.permissions.values_list('codename', flat=True))
            if not user_permissions.intersection(menu_permissions):
                return False
        
        return True
    
    @classmethod
    def _build_menu_tree(cls, menus: List[Menu], user: User) -> List[Dict[str, Any]]:
        """构建菜单树"""
        # 获取用户菜单配置
        user_configs = {
            config.menu_id: config 
            for config in UserMenuConfig.objects.filter(
                tenant=user.tenant, 
                user=user
            ).select_related('menu')
        }
        
        # 按层级分组
        menu_dict = {}
        root_menus = []
        
        for menu in menus:
            menu_data = cls._serialize_menu(menu, user_configs.get(menu.id))
            menu_dict[menu.id] = menu_data
            
            if menu.parent_id is None:
                root_menus.append(menu_data)
        
        # 构建父子关系
        for menu in menus:
            if menu.parent_id and menu.parent_id in menu_dict:
                parent = menu_dict[menu.parent_id]
                if 'children' not in parent:
                    parent['children'] = []
                parent['children'].append(menu_dict[menu.id])
        
        # 排序
        cls._sort_menus(root_menus)
        
        return root_menus
    
    @classmethod
    def _serialize_menu(cls, menu: Menu, user_config: Optional[UserMenuConfig] = None) -> Dict[str, Any]:
        """序列化菜单数据"""
        data = {
            'id': menu.id,
            'name': menu.name,
            'title': menu.title,
            'icon': menu.icon,
            'path': menu.path,
            'component': menu.component,
            'menu_type': menu.menu_type,
            'target': menu.target,
            'level': menu.level,
            'sort_order': menu.sort_order,
            'meta': menu.meta_info,
            'children': []
        }
        
        # 应用用户自定义配置
        if user_config:
            if user_config.custom_title:
                data['title'] = user_config.custom_title
            if user_config.custom_icon:
                data['icon'] = user_config.custom_icon
            if user_config.custom_sort:
                data['sort_order'] = user_config.custom_sort
            
            data['is_favorite'] = user_config.is_favorite
            data['is_hidden'] = user_config.is_hidden
        
        return data
    
    @classmethod
    def _sort_menus(cls, menus: List[Dict[str, Any]]):
        """递归排序菜单"""
        menus.sort(key=lambda x: (x['sort_order'], x['id']))
        
        for menu in menus:
            if menu.get('children'):
                cls._sort_menus(menu['children'])
    
    @classmethod
    def create_menu(cls, tenant, data: Dict[str, Any]) -> Menu:
        """创建菜单"""
        with transaction.atomic():
            menu = Menu.objects.create(
                tenant=tenant,
                name=data['name'],
                title=data['title'],
                icon=data.get('icon', ''),
                path=data.get('path', ''),
                component=data.get('component', ''),
                parent_id=data.get('parent_id'),
                menu_type=data.get('menu_type', 'menu'),
                target=data.get('target', '_self'),
                sort_order=data.get('sort_order', 0),
                is_visible=data.get('is_visible', True),
                is_enabled=data.get('is_enabled', True),
                is_cache=data.get('is_cache', True),
                meta_info=data.get('meta_info', {})
            )
            
            # 设置权限
            if 'permissions' in data:
                menu.permissions.set(data['permissions'])
            
            if 'roles' in data:
                menu.roles.set(data['roles'])
            
            # 清除缓存
            cls._clear_menu_cache(tenant)
            
            return menu
    
    @classmethod
    def update_menu(cls, menu: Menu, data: Dict[str, Any]) -> Menu:
        """更新菜单"""
        with transaction.atomic():
            # 更新基本信息
            for field in ['name', 'title', 'icon', 'path', 'component', 
                         'menu_type', 'target', 'sort_order', 'is_visible', 
                         'is_enabled', 'is_cache', 'meta_info']:
                if field in data:
                    setattr(menu, field, data[field])
            
            # 更新父菜单
            if 'parent_id' in data:
                menu.parent_id = data['parent_id']
            
            menu.save()
            
            # 更新权限
            if 'permissions' in data:
                menu.permissions.set(data['permissions'])
            
            if 'roles' in data:
                menu.roles.set(data['roles'])
            
            # 清除缓存
            cls._clear_menu_cache(menu.tenant)
            
            return menu
    
    @classmethod
    def delete_menu(cls, menu: Menu):
        """删除菜单"""
        with transaction.atomic():
            tenant = menu.tenant
            
            # 检查是否有子菜单
            if menu.children.exists():
                raise ValueError("存在子菜单，无法删除")
            
            menu.delete()
            
            # 清除缓存
            cls._clear_menu_cache(tenant)
    
    @classmethod
    def reorder_menus(cls, tenant, menu_orders: List[Dict[str, Any]]):
        """重新排序菜单"""
        with transaction.atomic():
            for item in menu_orders:
                Menu.objects.filter(
                    tenant=tenant,
                    id=item['id']
                ).update(
                    sort_order=item['sort_order'],
                    parent_id=item.get('parent_id')
                )
            
            # 清除缓存
            cls._clear_menu_cache(tenant)
    
    @classmethod
    def get_menu_tree_for_admin(cls, tenant) -> List[Dict[str, Any]]:
        """获取管理员菜单树（包含所有菜单）"""
        menus = Menu.objects.filter(tenant=tenant).select_related('parent')
        
        menu_dict = {}
        root_menus = []
        
        for menu in menus:
            menu_data = {
                'id': menu.id,
                'name': menu.name,
                'title': menu.title,
                'icon': menu.icon,
                'path': menu.path,
                'component': menu.component,
                'menu_type': menu.menu_type,
                'target': menu.target,
                'level': menu.level,
                'sort_order': menu.sort_order,
                'is_visible': menu.is_visible,
                'is_enabled': menu.is_enabled,
                'parent_id': menu.parent_id,
                'permissions': list(menu.permissions.values_list('id', flat=True)),
                'roles': list(menu.roles.values_list('id', flat=True)),
                'meta': menu.meta_info,
                'children': []
            }
            
            menu_dict[menu.id] = menu_data
            
            if menu.parent_id is None:
                root_menus.append(menu_data)
        
        # 构建父子关系
        for menu in menus:
            if menu.parent_id and menu.parent_id in menu_dict:
                parent = menu_dict[menu.parent_id]
                parent['children'].append(menu_dict[menu.id])
        
        # 排序
        cls._sort_menus(root_menus)
        
        return root_menus
    
    @classmethod
    def update_user_menu_config(cls, user: User, menu_id: int, config_data: Dict[str, Any]):
        """更新用户菜单配置"""
        menu = Menu.objects.get(tenant=user.tenant, id=menu_id)
        
        user_config, created = UserMenuConfig.objects.get_or_create(
            tenant=user.tenant,
            user=user,
            menu=menu,
            defaults=config_data
        )
        
        if not created:
            for field, value in config_data.items():
                setattr(user_config, field, value)
            user_config.save()
        
        # 清除用户菜单缓存
        cache_key = f"user_menus_{user.tenant.id}_{user.id}"
        cache.delete(cache_key)
        
        return user_config
    
    @classmethod
    def record_menu_access(cls, user: User, menu_id: int):
        """记录菜单访问"""
        try:
            config = UserMenuConfig.objects.get(
                tenant=user.tenant,
                user=user,
                menu_id=menu_id
            )
            config.access_count += 1
            config.last_access_time = timezone.now()
            config.save(update_fields=['access_count', 'last_access_time'])
        except UserMenuConfig.DoesNotExist:
            # 创建访问记录
            menu = Menu.objects.get(tenant=user.tenant, id=menu_id)
            UserMenuConfig.objects.create(
                tenant=user.tenant,
                user=user,
                menu=menu,
                access_count=1,
                last_access_time=timezone.now()
            )
    
    @classmethod
    def get_user_favorite_menus(cls, user: User) -> List[Dict[str, Any]]:
        """获取用户收藏的菜单"""
        configs = UserMenuConfig.objects.filter(
            tenant=user.tenant,
            user=user,
            is_favorite=True
        ).select_related('menu').order_by('-last_access_time')
        
        return [
            {
                'id': config.menu.id,
                'name': config.menu.name,
                'title': config.custom_title or config.menu.title,
                'icon': config.custom_icon or config.menu.icon,
                'path': config.menu.path,
                'access_count': config.access_count,
                'last_access_time': config.last_access_time
            }
            for config in configs
        ]
    
    @classmethod
    def _clear_menu_cache(cls, tenant):
        """清除菜单相关缓存"""
        # 清除所有用户的菜单缓存
        from django.core.cache import cache
        from ..users.models import User
        
        # 清除所有用户的菜单缓存
        users = User.objects.filter(tenant=tenant)
        for user in users:
            cache_key = f"user_menus_{tenant.id}_{user.id}"
            cache.delete(cache_key)
        
        # 清除权限缓存表
        MenuPermissionCache.objects.filter(user__tenant=tenant).delete()
        
        # 清除菜单树缓存
        cache.delete(f"menu_tree_{tenant.id}")
        cache.delete(f"admin_menu_tree_{tenant.id}")
    
    @classmethod
    def warm_up_cache(cls, tenant):
        """预热菜单缓存"""
        from ..users.models import User
        
        # 预热管理员菜单树
        cls.get_menu_tree_for_admin(tenant)
        
        # 为活跃用户预热菜单缓存
        active_users = User.objects.filter(
            tenant=tenant, 
            is_active=True
        ).select_related('tenant')[:50]  # 限制预热用户数量
        
        for user in active_users:
            try:
                cls.get_user_menus(user, use_cache=True)
            except Exception as e:
                # 记录错误但不中断预热过程
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"预热用户 {user.username} 菜单缓存失败: {e}")
    
    @classmethod
    def get_menu_performance_stats(cls, tenant):
        """获取菜单性能统计"""
        from django.db import connection
        from django.core.cache import cache
        
        stats = {
            'total_menus': Menu.objects.filter(tenant=tenant).count(),
            'cache_hit_rate': 0,
            'avg_query_time': 0,
            'cache_size': 0
        }
        
        # 计算缓存命中率（简化实现）
        cache_keys = [
            f"menu_tree_{tenant.id}",
            f"admin_menu_tree_{tenant.id}"
        ]
        
        hit_count = 0
        for key in cache_keys:
            if cache.get(key) is not None:
                hit_count += 1
        
        stats['cache_hit_rate'] = (hit_count / len(cache_keys)) * 100 if cache_keys else 0
        
        return stats