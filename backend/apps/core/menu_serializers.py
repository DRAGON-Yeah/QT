# -*- coding: utf-8 -*-
"""
菜单管理序列化器
"""
from rest_framework import serializers
from django.contrib.auth.models import Permission
from .models import Menu, UserMenuConfig
from ..users.models import Role


class MenuSerializer(serializers.ModelSerializer):
    """菜单序列化器"""
    
    children = serializers.SerializerMethodField()
    permission_names = serializers.SerializerMethodField()
    role_names = serializers.SerializerMethodField()
    has_children = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Menu
        fields = [
            'id', 'name', 'title', 'icon', 'path', 'component',
            'parent', 'level', 'sort_order', 'menu_type', 'target',
            'permissions', 'roles', 'is_visible', 'is_enabled', 'is_cache',
            'meta_info', 'created_at', 'updated_at',
            'children', 'permission_names', 'role_names', 'has_children', 'full_path'
        ]
        read_only_fields = ['level', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        """获取子菜单"""
        if hasattr(obj, '_prefetched_children'):
            children = [child for child in obj._prefetched_children if child.is_visible]
        else:
            children = obj.children.filter(is_visible=True).order_by('sort_order')
        
        return MenuSerializer(children, many=True, context=self.context).data
    
    def get_permission_names(self, obj):
        """获取权限名称列表"""
        return list(obj.permissions.values_list('name', flat=True))
    
    def get_role_names(self, obj):
        """获取角色名称列表"""
        return list(obj.roles.values_list('name', flat=True))
    
    def get_has_children(self, obj):
        """是否有子菜单"""
        return obj.has_children()
    
    def get_full_path(self, obj):
        """获取完整路径"""
        return obj.get_full_path()
    
    def validate_name(self, value):
        """验证菜单名称唯一性"""
        tenant = self.context['request'].user.tenant
        queryset = Menu.objects.filter(tenant=tenant, name=value)
        
        if self.instance:
            queryset = queryset.exclude(id=self.instance.id)
        
        if queryset.exists():
            raise serializers.ValidationError("菜单名称已存在")
        
        return value
    
    def validate_parent(self, value):
        """验证父菜单"""
        if value and self.instance and value.id == self.instance.id:
            raise serializers.ValidationError("不能将自己设为父菜单")
        
        # 检查循环引用
        if value and self.instance:
            current = value
            while current:
                if current.id == self.instance.id:
                    raise serializers.ValidationError("不能创建循环引用")
                current = current.parent
        
        return value
    
    def create(self, validated_data):
        """创建菜单"""
        tenant = self.context['request'].user.tenant
        validated_data['tenant'] = tenant
        
        # 处理多对多字段
        permissions = validated_data.pop('permissions', [])
        roles = validated_data.pop('roles', [])
        
        menu = Menu.objects.create(**validated_data)
        
        if permissions:
            menu.permissions.set(permissions)
        if roles:
            menu.roles.set(roles)
        
        return menu


class MenuTreeSerializer(serializers.ModelSerializer):
    """菜单树序列化器（用于前端显示）"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Menu
        fields = [
            'id', 'name', 'title', 'icon', 'path', 'component',
            'menu_type', 'target', 'level', 'sort_order', 'meta_info',
            'children'
        ]
    
    def get_children(self, obj):
        """获取子菜单"""
        children = getattr(obj, 'children_list', [])
        return MenuTreeSerializer(children, many=True).data


class MenuCreateSerializer(serializers.ModelSerializer):
    """菜单创建序列化器"""
    
    class Meta:
        model = Menu
        fields = [
            'name', 'title', 'icon', 'path', 'component',
            'parent', 'menu_type', 'target', 'sort_order',
            'permissions', 'roles', 'is_visible', 'is_enabled', 'is_cache',
            'meta_info'
        ]
    
    def validate_name(self, value):
        """验证菜单名称"""
        if not value or not value.strip():
            raise serializers.ValidationError("菜单名称不能为空")
        
        # 检查名称格式
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError("菜单名称只能包含字母、数字和下划线，且必须以字母开头")
        
        return value.strip()
    
    def validate_path(self, value):
        """验证路由路径"""
        if value and not value.startswith('/'):
            raise serializers.ValidationError("路由路径必须以 / 开头")
        
        return value


class MenuUpdateSerializer(serializers.ModelSerializer):
    """菜单更新序列化器"""
    
    class Meta:
        model = Menu
        fields = [
            'title', 'icon', 'path', 'component',
            'parent', 'menu_type', 'target', 'sort_order',
            'permissions', 'roles', 'is_visible', 'is_enabled', 'is_cache',
            'meta_info'
        ]


class MenuReorderSerializer(serializers.Serializer):
    """菜单重排序序列化器"""
    
    menus = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    
    def validate_menus(self, value):
        """验证菜单排序数据"""
        if not value:
            raise serializers.ValidationError("菜单数据不能为空")
        
        required_fields = ['id', 'sort_order']
        for item in value:
            for field in required_fields:
                if field not in item:
                    raise serializers.ValidationError(f"缺少必需字段: {field}")
        
        return value


class UserMenuConfigSerializer(serializers.ModelSerializer):
    """用户菜单配置序列化器"""
    
    menu_title = serializers.CharField(source='menu.title', read_only=True)
    menu_icon = serializers.CharField(source='menu.icon', read_only=True)
    menu_path = serializers.CharField(source='menu.path', read_only=True)
    
    class Meta:
        model = UserMenuConfig
        fields = [
            'id', 'menu', 'is_favorite', 'is_hidden',
            'custom_title', 'custom_icon', 'custom_sort',
            'access_count', 'last_access_time',
            'menu_title', 'menu_icon', 'menu_path'
        ]
        read_only_fields = ['access_count', 'last_access_time']


class PermissionSerializer(serializers.ModelSerializer):
    """权限序列化器"""
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'content_type']


class RoleSerializer(serializers.ModelSerializer):
    """角色序列化器"""
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description']


class MenuIconSerializer(serializers.Serializer):
    """菜单图标序列化器"""
    
    category = serializers.CharField(max_length=50)
    icons = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )


class MenuStatsSerializer(serializers.Serializer):
    """菜单统计序列化器"""
    
    total_menus = serializers.IntegerField()
    visible_menus = serializers.IntegerField()
    enabled_menus = serializers.IntegerField()
    menu_levels = serializers.IntegerField()
    most_accessed = serializers.ListField(
        child=serializers.DictField()
    )