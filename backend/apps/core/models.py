"""
核心模型 - 多租户基础模型
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone


class Tenant(models.Model):
    """
    租户模型 - 多租户架构的核心
    每个租户拥有独立的数据空间
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('租户名称', max_length=100, unique=True)
    schema_name = models.CharField('数据库模式名', max_length=63, unique=True)
    domain = models.CharField('域名', max_length=100, blank=True, null=True)
    is_active = models.BooleanField('是否激活', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    # 租户配置
    max_users = models.PositiveIntegerField('最大用户数', default=100)
    max_strategies = models.PositiveIntegerField('最大策略数', default=50)
    max_exchange_accounts = models.PositiveIntegerField('最大交易所账户数', default=10)
    
    # 租户状态
    subscription_expires_at = models.DateTimeField('订阅到期时间', null=True, blank=True)
    
    class Meta:
        db_table = 'core_tenant'
        verbose_name = '租户'
        verbose_name_plural = '租户'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """验证租户数据"""
        if self.schema_name:
            # 确保schema_name符合数据库命名规范
            if not self.schema_name.isidentifier():
                raise ValidationError('数据库模式名必须是有效的标识符')
    
    def is_subscription_active(self):
        """检查订阅是否有效"""
        if not self.subscription_expires_at:
            return True
        return timezone.now() < self.subscription_expires_at
    
    def get_user_count(self):
        """获取租户用户数量"""
        return self.users.filter(is_active=True).count()
    
    def can_add_user(self):
        """检查是否可以添加新用户"""
        return self.get_user_count() < self.max_users


class TenantManager(models.Manager):
    """
    租户管理器 - 自动过滤当前租户的数据
    """
    def get_queryset(self):
        from .utils import get_current_tenant
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        return super().get_queryset()
    
    def all_tenants(self):
        """获取所有租户的数据（不过滤）"""
        return super().get_queryset()


class TenantModel(models.Model):
    """
    多租户基础模型 - 所有需要租户隔离的模型都应该继承此模型
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        verbose_name='租户',
        related_name='%(class)s_set'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    # 使用租户管理器
    objects = TenantManager()
    all_objects = models.Manager()  # 不过滤租户的管理器，仅供管理员使用
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """保存时自动设置租户"""
        if not self.tenant_id:
            from .utils import get_current_tenant
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ValidationError('无法确定当前租户，请确保在租户上下文中操作')
        super().save(*args, **kwargs)


class Permission(models.Model):
    """
    权限模型 - 定义系统中的各种权限
    """
    name = models.CharField('权限名称', max_length=100)
    codename = models.CharField('权限代码', max_length=100, unique=True)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='内容类型',
        null=True,
        blank=True,
        related_name='custom_permissions'
    )
    description = models.TextField('权限描述', blank=True)
    
    # 权限分类
    CATEGORY_CHOICES = [
        ('system', '系统管理'),
        ('user', '用户管理'),
        ('trading', '交易管理'),
        ('strategy', '策略管理'),
        ('risk', '风险控制'),
        ('market', '市场数据'),
        ('monitoring', '系统监控'),
    ]
    category = models.CharField('权限分类', max_length=20, choices=CATEGORY_CHOICES)
    
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    
    class Meta:
        db_table = 'core_permission'
        verbose_name = '权限'
        verbose_name_plural = '权限'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.codename})"


class Role(TenantModel):
    """
    角色模型 - 权限的集合，支持租户级别的角色定义
    """
    name = models.CharField('角色名称', max_length=50)
    description = models.TextField('角色描述', blank=True)
    permissions = models.ManyToManyField(
        Permission,
        verbose_name='权限',
        blank=True,
        related_name='roles'
    )
    
    # 角色类型
    ROLE_TYPE_CHOICES = [
        ('system', '系统预定义'),
        ('custom', '自定义角色'),
    ]
    role_type = models.CharField('角色类型', max_length=10, choices=ROLE_TYPE_CHOICES, default='custom')
    
    # 角色层级（用于权限继承）
    parent_role = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='父角色',
        related_name='child_roles'
    )
    
    # 角色优先级（数字越大优先级越高）
    priority = models.PositiveIntegerField('优先级', default=0)
    
    # 角色颜色标识
    color = models.CharField('颜色标识', max_length=7, default='#1890FF')
    
    is_active = models.BooleanField('是否激活', default=True)
    
    class Meta:
        db_table = 'core_role'
        verbose_name = '角色'
        verbose_name_plural = '角色'
        unique_together = ['tenant', 'name']
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.tenant.name})"
    
    def clean(self):
        """
        验证角色数据
        
        主要验证：
        - 防止循环继承（角色A继承角色B，角色B又继承角色A）
        - 确保角色层级结构的合理性
        """
        super().clean()
        
        # 防止循环继承
        if self.parent_role:
            if self._check_circular_inheritance(self.parent_role):
                raise ValidationError('不能设置循环继承的父角色')
    
    def _check_circular_inheritance(self, parent):
        """
        检查是否存在循环继承
        
        参数:
            parent: 父角色对象
            
        返回:
            bool: 如果存在循环继承返回True，否则返回False
            
        算法:
            递归检查父角色链，如果发现当前角色在父角色链中则存在循环
        """
        if parent == self:
            return True
        if parent.parent_role:
            return self._check_circular_inheritance(parent.parent_role)
        return False
    
    def get_all_permissions(self):
        """获取角色的所有权限（包括继承的权限）"""
        permissions = set(self.permissions.all())
        
        # 递归获取父角色的权限
        if self.parent_role:
            permissions.update(self.parent_role.get_all_permissions())
        
        return permissions
    
    def get_inherited_permissions(self):
        """获取从父角色继承的权限"""
        if not self.parent_role:
            return set()
        
        return self.parent_role.get_all_permissions()
    
    def get_direct_permissions(self):
        """获取角色直接拥有的权限"""
        return set(self.permissions.all())
    
    def has_permission(self, permission_codename):
        """检查角色是否拥有指定权限"""
        all_permissions = self.get_all_permissions()
        return any(perm.codename == permission_codename for perm in all_permissions)
    
    def get_inheritance_chain(self):
        """
        获取角色继承链
        
        返回:
            list: 从当前角色到根角色的完整继承链
            
        示例:
            如果角色层级为：观察者 -> 交易员 -> 管理员
            则返回：[观察者, 交易员, 管理员]
        """
        chain = [self]
        current = self.parent_role
        while current:
            chain.append(current)
            current = current.parent_role
        return chain
    
    def get_child_roles(self):
        """
        获取所有激活的子角色
        
        返回:
            QuerySet: 当前角色的所有激活子角色
        """
        return self.child_roles.filter(is_active=True)
    
    def can_be_deleted(self):
        """
        检查角色是否可以被删除
        
        返回:
            tuple: (是否可删除, 原因说明)
            
        删除限制:
            1. 系统预定义角色不能删除
            2. 正在被用户使用的角色不能删除
            3. 有子角色的角色不能删除
        """
        # 系统预定义角色不能删除
        if self.role_type == 'system':
            return False, '系统预定义角色不能删除'
        
        # 检查是否有用户使用此角色
        if self.users.filter(is_active=True).exists():
            return False, '此角色正在被用户使用，无法删除'
        
        # 检查是否有子角色
        if self.child_roles.filter(is_active=True).exists():
            return False, '此角色有子角色，无法删除'
        
        return True, '可以删除'
    
    def get_user_count(self):
        """
        获取拥有此角色的用户数量
        
        返回:
            int: 激活用户数量
        """
        return self.users.filter(is_active=True).count()
    
    def copy_permissions_from(self, source_role):
        """
        从另一个角色复制权限
        
        参数:
            source_role: 源角色对象
            
        注意:
            - 会覆盖当前角色的所有权限
            - 不会复制角色的其他属性（如名称、描述等）
        """
        if source_role and source_role != self:
            self.permissions.set(source_role.permissions.all())
    
    @classmethod
    def create_system_roles(cls, tenant):
        """
        为租户创建系统预定义角色
        
        参数:
            tenant: 租户对象
            
        返回:
            list: 创建的角色列表
            
        创建的角色:
            1. 超级管理员 - 拥有所有权限，优先级100，红色标识
            2. 管理员 - 拥有大部分管理权限，优先级80，橙色标识
            3. 交易员 - 拥有交易相关权限，优先级60，绿色标识
            4. 观察者 - 只有查看权限，优先级20，蓝色标识
            
        注意:
            - 如果角色已存在则不会重复创建
            - 只有新创建的角色才会被返回
        """
        system_roles = [
            {
                'name': '超级管理员',
                'description': '拥有所有权限的超级管理员角色',
                'color': '#F5222D',  # 红色 - 最高权限
                'priority': 100,
                'permissions': Permission.objects.all()
            },
            {
                'name': '管理员',
                'description': '拥有大部分管理权限的管理员角色',
                'color': '#FA8C16',  # 橙色 - 高权限
                'priority': 80,
                'permissions': Permission.objects.filter(
                    category__in=['user', 'trading', 'strategy', 'risk']
                )
            },
            {
                'name': '交易员',
                'description': '拥有交易相关权限的交易员角色',
                'color': '#52C41A',  # 绿色 - 中等权限
                'priority': 60,
                'permissions': Permission.objects.filter(
                    category__in=['trading', 'market']
                )
            },
            {
                'name': '观察者',
                'description': '只有查看权限的观察者角色',
                'color': '#1890FF',  # 蓝色 - 基础权限
                'priority': 20,
                'permissions': Permission.objects.filter(
                    codename__contains='view'
                )
            }
        ]
        
        created_roles = []
        for role_data in system_roles:
            # 提取权限配置，避免在创建时传入
            permissions = role_data.pop('permissions')
            
            # 获取或创建角色
            role, created = cls.objects.get_or_create(
                tenant=tenant,
                name=role_data['name'],
                defaults={
                    **role_data,
                    'role_type': 'system'
                }
            )
            
            # 只为新创建的角色设置权限
            if created:
                role.permissions.set(permissions)
                created_roles.append(role)
        
        return created_roles


class Menu(TenantModel):
    """
    菜单模型 - 支持多级菜单结构和权限控制
    """
    MENU_TYPES = [
        ('menu', '菜单'),
        ('button', '按钮'),
        ('link', '链接'),
    ]
    
    TARGET_TYPES = [
        ('_self', '当前窗口'),
        ('_blank', '新窗口'),
    ]
    
    # 基本信息
    name = models.CharField('菜单名称', max_length=100)
    title = models.CharField('菜单标题', max_length=100)
    icon = models.CharField('图标', max_length=100, blank=True, help_text='图标类名或图标代码')
    path = models.CharField('路由路径', max_length=200, blank=True)
    component = models.CharField('组件路径', max_length=200, blank=True)
    
    # 层级关系
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='children', verbose_name='父菜单')
    level = models.PositiveIntegerField('菜单层级', default=1)
    sort_order = models.PositiveIntegerField('排序', default=0)
    
    # 菜单类型和属性
    menu_type = models.CharField('菜单类型', max_length=20, choices=MENU_TYPES, default='menu')
    target = models.CharField('打开方式', max_length=20, choices=TARGET_TYPES, default='_self')
    
    # 权限控制
    permissions = models.ManyToManyField('auth.Permission', blank=True, verbose_name='所需权限')
    roles = models.ManyToManyField('core.Role', blank=True, verbose_name='可访问角色')
    
    # 显示控制
    is_visible = models.BooleanField('是否显示', default=True)
    is_enabled = models.BooleanField('是否启用', default=True)
    is_cache = models.BooleanField('是否缓存', default=True)
    
    # 扩展属性
    meta_info = models.JSONField('元信息', default=dict, blank=True, 
                                help_text='存储额外的菜单配置信息')
    
    class Meta:
        db_table = 'core_menu'
        verbose_name = '菜单'
        verbose_name_plural = '菜单'
        ordering = ['level', 'sort_order', 'id']
        indexes = [
            models.Index(fields=['tenant', 'parent', 'level']),
            models.Index(fields=['tenant', 'is_visible', 'is_enabled']),
            models.Index(fields=['tenant', 'sort_order']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.name})"
    
    def save(self, *args, **kwargs):
        """保存时自动计算层级"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """获取完整路径"""
        if self.parent:
            return f"{self.parent.get_full_path()}/{self.path}"
        return self.path
    
    def get_breadcrumb(self):
        """获取面包屑导航"""
        breadcrumb = []
        current = self
        while current:
            breadcrumb.insert(0, {
                'id': current.id,
                'name': current.name,
                'title': current.title,
                'path': current.path
            })
            current = current.parent
        return breadcrumb
    
    def has_children(self):
        """是否有子菜单"""
        return self.children.filter(is_visible=True, is_enabled=True).exists()
    
    def get_children_count(self):
        """获取子菜单数量"""
        return self.children.filter(is_visible=True, is_enabled=True).count()


class UserMenuConfig(TenantModel):
    """用户菜单配置"""
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, verbose_name='菜单')
    
    # 个性化配置
    is_favorite = models.BooleanField('是否收藏', default=False)
    is_hidden = models.BooleanField('是否隐藏', default=False)
    custom_title = models.CharField('自定义标题', max_length=100, blank=True)
    custom_icon = models.CharField('自定义图标', max_length=100, blank=True)
    custom_sort = models.PositiveIntegerField('自定义排序', default=0)
    
    # 访问统计
    access_count = models.PositiveIntegerField('访问次数', default=0)
    last_access_time = models.DateTimeField('最后访问时间', null=True, blank=True)
    
    class Meta:
        db_table = 'core_user_menu_config'
        verbose_name = '用户菜单配置'
        verbose_name_plural = '用户菜单配置'
        unique_together = ['tenant', 'user', 'menu']
        indexes = [
            models.Index(fields=['tenant', 'user', 'is_favorite']),
            models.Index(fields=['tenant', 'user', 'is_hidden']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.menu.title}"


class MenuPermissionCache(models.Model):
    """菜单权限缓存"""
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    menu_permissions = models.JSONField('菜单权限', default=dict)
    cache_time = models.DateTimeField('缓存时间', auto_now=True)
    
    class Meta:
        db_table = 'core_menu_permission_cache'
        verbose_name = '菜单权限缓存'
        verbose_name_plural = '菜单权限缓存'
        unique_together = ['user']
    
    def is_expired(self, timeout=3600):
        """检查缓存是否过期"""
        from django.utils import timezone
        import datetime
        
        return (timezone.now() - self.cache_time).total_seconds() > timeout