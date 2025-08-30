# -*- coding: utf-8 -*-
"""
菜单管理视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import Permission
from django.db.models import Q, Count, Max
from django.db import models
from django.core.cache import cache
from django.utils import timezone

from .models import Menu, UserMenuConfig
from .menu_serializers import (
    MenuSerializer, MenuTreeSerializer, MenuCreateSerializer,
    MenuUpdateSerializer, MenuReorderSerializer, UserMenuConfigSerializer,
    PermissionSerializer, RoleSerializer, MenuStatsSerializer
)
from .menu_services import MenuService
from .permissions import TenantPermission
from ..users.models import Role


class MenuViewSet(viewsets.ModelViewSet):
    """菜单管理视图集"""
    
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """获取查询集"""
        return Menu.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('parent').prefetch_related('permissions', 'roles')
    
    def get_serializer_class(self):
        """获取序列化器类"""
        if self.action == 'create':
            return MenuCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MenuUpdateSerializer
        elif self.action == 'tree':
            return MenuTreeSerializer
        elif self.action == 'reorder':
            return MenuReorderSerializer
        return MenuSerializer
    
    def perform_create(self, serializer):
        """创建菜单"""
        serializer.save(tenant=self.request.user.tenant)
        
        # 清除菜单缓存
        MenuService._clear_menu_cache(self.request.user.tenant)
    
    def perform_update(self, serializer):
        """更新菜单"""
        serializer.save()
        
        # 清除菜单缓存
        MenuService._clear_menu_cache(self.request.user.tenant)
    
    def perform_destroy(self, instance):
        """删除菜单"""
        # 检查是否有子菜单
        if instance.children.exists():
            return Response(
                {'error': '存在子菜单，无法删除'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.delete()
        
        # 清除菜单缓存
        MenuService._clear_menu_cache(self.request.user.tenant)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取菜单树"""
        # 检查是否是管理员
        if request.user.is_superuser or request.user.has_perm('core.view_menu'):
            # 管理员获取完整菜单树
            menu_tree = MenuService.get_menu_tree_for_admin(request.user.tenant)
        else:
            # 普通用户获取有权限的菜单树
            menu_tree = MenuService.get_user_menus(request.user)
        
        return Response(menu_tree)
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """重新排序菜单"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            MenuService.reorder_menus(
                request.user.tenant,
                serializer.validated_data['menus']
            )
            return Response({'message': '菜单排序成功'})
        except Exception as e:
            return Response(
                {'error': f'菜单排序失败: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def toggle_visibility(self, request, pk=None):
        """切换菜单可见性"""
        menu = self.get_object()
        menu.is_visible = not menu.is_visible
        menu.save()
        
        # 清除菜单缓存
        MenuService._clear_menu_cache(request.user.tenant)
        
        return Response({
            'message': f'菜单已{"显示" if menu.is_visible else "隐藏"}',
            'is_visible': menu.is_visible
        })
    
    @action(detail=True, methods=['post'])
    def toggle_enabled(self, request, pk=None):
        """切换菜单启用状态"""
        menu = self.get_object()
        menu.is_enabled = not menu.is_enabled
        menu.save()
        
        # 清除菜单缓存
        MenuService._clear_menu_cache(request.user.tenant)
        
        return Response({
            'message': f'菜单已{"启用" if menu.is_enabled else "禁用"}',
            'is_enabled': menu.is_enabled
        })
    
    @action(detail=False, methods=['get'])
    def permissions(self, request):
        """获取所有权限"""
        permissions = Permission.objects.all().select_related('content_type')
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def roles(self, request):
        """获取所有角色"""
        roles = Role.objects.filter(tenant=request.user.tenant)
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def icons(self, request):
        """获取可用图标"""
        # 这里可以返回系统支持的图标列表
        icons = {
            'common': [
                {'name': 'dashboard', 'class': 'fas fa-tachometer-alt', 'unicode': '\\f3fd'},
                {'name': 'user', 'class': 'fas fa-user', 'unicode': '\\f007'},
                {'name': 'users', 'class': 'fas fa-users', 'unicode': '\\f0c0'},
                {'name': 'settings', 'class': 'fas fa-cog', 'unicode': '\\f013'},
                {'name': 'chart', 'class': 'fas fa-chart-line', 'unicode': '\\f201'},
                {'name': 'table', 'class': 'fas fa-table', 'unicode': '\\f0ce'},
                {'name': 'file', 'class': 'fas fa-file', 'unicode': '\\f15b'},
                {'name': 'folder', 'class': 'fas fa-folder', 'unicode': '\\f07b'},
            ],
            'trading': [
                {'name': 'exchange', 'class': 'fas fa-exchange-alt', 'unicode': '\\f362'},
                {'name': 'coins', 'class': 'fas fa-coins', 'unicode': '\\f51e'},
                {'name': 'chart-bar', 'class': 'fas fa-chart-bar', 'unicode': '\\f080'},
                {'name': 'calculator', 'class': 'fas fa-calculator', 'unicode': '\\f1ec'},
                {'name': 'shield', 'class': 'fas fa-shield-alt', 'unicode': '\\f3ed'},
            ],
            'system': [
                {'name': 'server', 'class': 'fas fa-server', 'unicode': '\\f233'},
                {'name': 'database', 'class': 'fas fa-database', 'unicode': '\\f1c0'},
                {'name': 'terminal', 'class': 'fas fa-terminal', 'unicode': '\\f120'},
                {'name': 'monitor', 'class': 'fas fa-desktop', 'unicode': '\\f108'},
                {'name': 'log', 'class': 'fas fa-file-alt', 'unicode': '\\f15c'},
            ]
        }
        
        return Response(icons)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取菜单统计信息"""
        tenant = request.user.tenant
        
        # 基本统计
        total_menus = Menu.objects.filter(tenant=tenant).count()
        visible_menus = Menu.objects.filter(tenant=tenant, is_visible=True).count()
        enabled_menus = Menu.objects.filter(tenant=tenant, is_enabled=True).count()
        menu_levels = Menu.objects.filter(tenant=tenant).aggregate(
            max_level=models.Max('level')
        )['max_level'] or 0
        
        # 最常访问的菜单
        most_accessed = UserMenuConfig.objects.filter(
            tenant=tenant,
            access_count__gt=0
        ).select_related('menu').order_by('-access_count')[:10]
        
        most_accessed_data = [
            {
                'menu_id': config.menu.id,
                'menu_title': config.menu.title,
                'access_count': config.access_count,
                'last_access_time': config.last_access_time
            }
            for config in most_accessed
        ]
        
        stats_data = {
            'total_menus': total_menus,
            'visible_menus': visible_menus,
            'enabled_menus': enabled_menus,
            'menu_levels': menu_levels,
            'most_accessed': most_accessed_data
        }
        
        serializer = MenuStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出菜单配置"""
        from django.http import JsonResponse
        import json
        
        tenant = request.user.tenant
        menu_tree = MenuService.get_menu_tree_for_admin(tenant)
        
        export_data = {
            'version': '1.0',
            'tenant': tenant.name,
            'export_time': timezone.now().isoformat(),
            'menus': menu_tree
        }
        
        response = JsonResponse(export_data, json_dumps_params={'ensure_ascii': False, 'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="menus_{tenant.name}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json"'
        return response
    
    @action(detail=False, methods=['post'])
    def import_menus(self, request):
        """导入菜单配置"""
        import json
        from django.db import transaction
        
        try:
            # 获取上传的文件或JSON数据
            if 'file' in request.FILES:
                file_content = request.FILES['file'].read().decode('utf-8')
                import_data = json.loads(file_content)
            else:
                import_data = request.data
            
            # 验证导入数据格式
            if 'menus' not in import_data:
                return Response({'error': '无效的导入数据格式'}, status=status.HTTP_400_BAD_REQUEST)
            
            tenant = request.user.tenant
            
            # 导入选项
            options = {
                'clear_existing': request.data.get('clear_existing', False),
                'update_existing': request.data.get('update_existing', True),
                'import_permissions': request.data.get('import_permissions', False)
            }
            
            with transaction.atomic():
                imported_count = self._import_menu_data(tenant, import_data['menus'], options)
            
            # 清除缓存
            MenuService._clear_menu_cache(tenant)
            
            return Response({
                'message': f'成功导入 {imported_count} 个菜单',
                'imported_count': imported_count
            })
            
        except json.JSONDecodeError:
            return Response({'error': '无效的JSON格式'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'导入失败: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    
    def _import_menu_data(self, tenant, menus_data, options, parent=None):
        """递归导入菜单数据"""
        imported_count = 0
        
        for menu_data in menus_data:
            # 检查菜单是否已存在
            existing_menu = None
            if options['update_existing']:
                try:
                    existing_menu = Menu.objects.get(tenant=tenant, name=menu_data['name'])
                except Menu.DoesNotExist:
                    pass
            
            # 准备菜单数据
            menu_fields = {
                'tenant': tenant,
                'name': menu_data['name'],
                'title': menu_data['title'],
                'icon': menu_data.get('icon', ''),
                'path': menu_data.get('path', ''),
                'component': menu_data.get('component', ''),
                'parent': parent,
                'menu_type': menu_data.get('menu_type', 'menu'),
                'target': menu_data.get('target', '_self'),
                'sort_order': menu_data.get('sort_order', 0),
                'is_visible': menu_data.get('is_visible', True),
                'is_enabled': menu_data.get('is_enabled', True),
                'is_cache': menu_data.get('is_cache', True),
                'meta_info': menu_data.get('meta_info', {})
            }
            
            if existing_menu:
                # 更新现有菜单
                for field, value in menu_fields.items():
                    if field != 'tenant':  # 不更新租户字段
                        setattr(existing_menu, field, value)
                existing_menu.save()
                menu = existing_menu
            else:
                # 创建新菜单
                menu = Menu.objects.create(**menu_fields)
            
            imported_count += 1
            
            # 递归导入子菜单
            if 'children' in menu_data and menu_data['children']:
                imported_count += self._import_menu_data(
                    tenant, 
                    menu_data['children'], 
                    options, 
                    parent=menu
                )
        
        return imported_count
    
    @action(detail=False, methods=['post'])
    def warm_cache(self, request):
        """预热菜单缓存"""
        tenant = request.user.tenant
        
        try:
            MenuService.warm_up_cache(tenant)
            return Response({'message': '缓存预热完成'})
        except Exception as e:
            return Response(
                {'error': f'缓存预热失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance(self, request):
        """获取菜单性能统计"""
        tenant = request.user.tenant
        stats = MenuService.get_menu_performance_stats(tenant)
        return Response(stats)


class UserMenuConfigViewSet(viewsets.ModelViewSet):
    """用户菜单配置视图集"""
    
    serializer_class = UserMenuConfigSerializer
    permission_classes = [IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """获取查询集"""
        return UserMenuConfig.objects.filter(
            tenant=self.request.user.tenant,
            user=self.request.user
        ).select_related('menu')
    
    def perform_create(self, serializer):
        """创建用户菜单配置"""
        serializer.save(
            tenant=self.request.user.tenant,
            user=self.request.user
        )
        
        # 清除用户菜单缓存
        cache_key = f"user_menus_{self.request.user.tenant.id}_{self.request.user.id}"
        cache.delete(cache_key)
    
    def perform_update(self, serializer):
        """更新用户菜单配置"""
        serializer.save()
        
        # 清除用户菜单缓存
        cache_key = f"user_menus_{self.request.user.tenant.id}_{self.request.user.id}"
        cache.delete(cache_key)
    
    @action(detail=False, methods=['get'])
    def favorites(self, request):
        """获取收藏的菜单"""
        favorites = MenuService.get_user_favorite_menus(request.user)
        return Response(favorites)
    
    @action(detail=True, methods=['post'])
    def toggle_favorite(self, request, pk=None):
        """切换菜单收藏状态"""
        config = self.get_object()
        config.is_favorite = not config.is_favorite
        config.save()
        
        # 清除用户菜单缓存
        cache_key = f"user_menus_{request.user.tenant.id}_{request.user.id}"
        cache.delete(cache_key)
        
        return Response({
            'message': f'菜单已{"收藏" if config.is_favorite else "取消收藏"}',
            'is_favorite': config.is_favorite
        })
    
    @action(detail=True, methods=['post'])
    def access(self, request, pk=None):
        """记录菜单访问"""
        menu_id = pk
        MenuService.record_menu_access(request.user, menu_id)
        
        return Response({'message': '访问记录已更新'})
    
    @action(detail=False, methods=['post'])
    def batch_config(self, request):
        """批量配置菜单"""
        configs = request.data.get('configs', [])
        
        for config_data in configs:
            menu_id = config_data.get('menu_id')
            if menu_id:
                MenuService.update_user_menu_config(
                    request.user,
                    menu_id,
                    {
                        'is_favorite': config_data.get('is_favorite', False),
                        'is_hidden': config_data.get('is_hidden', False),
                        'custom_title': config_data.get('custom_title', ''),
                        'custom_icon': config_data.get('custom_icon', ''),
                        'custom_sort': config_data.get('custom_sort', 0)
                    }
                )
        
        return Response({'message': '批量配置成功'})