"""
用户模型 - 多租户用户管理
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import TenantModel, Tenant, Role


class User(AbstractUser):
    """
    自定义用户模型 - 支持多租户
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 租户关联
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        verbose_name='租户',
        related_name='users'
    )
    
    # 扩展用户信息
    phone = models.CharField('手机号', max_length=20, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    
    # 用户状态
    is_tenant_admin = models.BooleanField('是否为租户管理员', default=False)
    last_login_ip = models.GenericIPAddressField('最后登录IP', blank=True, null=True)
    last_activity = models.DateTimeField('最后活动时间', null=True, blank=True)
    
    # 角色关联
    roles = models.ManyToManyField(
        'core.Role',
        verbose_name='角色',
        blank=True,
        related_name='users',
        through='UserRole',
        through_fields=('user', 'role')
    )
    
    # 用户设置
    language = models.CharField('语言', max_length=10, default='zh-hans')
    timezone_name = models.CharField('时区', max_length=50, default='Asia/Shanghai')
    
    # 安全设置
    password_changed_at = models.DateTimeField('密码修改时间', null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField('登录失败次数', default=0)
    locked_until = models.DateTimeField('锁定到', null=True, blank=True)
    
    class Meta:
        db_table = 'users_user'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        unique_together = ['tenant', 'username']
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.tenant.name})"
    
    def clean(self):
        """验证用户数据"""
        super().clean()
        
        # 验证租户用户数量限制
        if not self.pk and self.tenant:
            if not self.tenant.can_add_user():
                raise ValidationError(f'租户用户数量已达到上限 ({self.tenant.max_users})')
    
    def save(self, *args, **kwargs):
        """保存用户"""
        # 设置密码修改时间
        if self.pk:
            try:
                old_user = User.objects.get(pk=self.pk)
                if old_user.password != self.password:
                    self.password_changed_at = timezone.now()
            except User.DoesNotExist:
                self.password_changed_at = timezone.now()
        else:
            self.password_changed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def get_all_permissions(self):
        """获取用户的所有权限（包括角色权限）"""
        permissions = set()
        
        # 获取用户直接权限（如果有的话）
        if hasattr(self, 'user_permissions'):
            permissions.update(self.user_permissions.values_list('codename', flat=True))
        
        # 获取角色权限
        for role in self.roles.filter(is_active=True):
            role_permissions = role.get_all_permissions()
            permissions.update(perm.codename for perm in role_permissions)
        
        return permissions
    
    def has_permission(self, permission_codename):
        """检查用户是否拥有指定权限"""
        # 超级用户拥有所有权限
        if self.is_superuser:
            return True
        
        # 租户管理员拥有租户内的所有权限
        if self.is_tenant_admin:
            return True
        
        # 检查具体权限
        all_permissions = self.get_all_permissions()
        return permission_codename in all_permissions
    
    def has_role(self, role_name):
        """检查用户是否拥有指定角色"""
        return self.roles.filter(name=role_name, is_active=True).exists()
    
    def add_role(self, role):
        """添加角色"""
        if isinstance(role, str):
            role = Role.objects.get(name=role, tenant=self.tenant)
        
        UserRole.objects.get_or_create(
            user=self,
            role=role,
            defaults={'assigned_by': None}  # 可以记录是谁分配的
        )
    
    def remove_role(self, role):
        """移除角色"""
        if isinstance(role, str):
            role = Role.objects.get(name=role, tenant=self.tenant)
        
        UserRole.objects.filter(user=self, role=role).delete()
    
    def is_account_locked(self):
        """检查账户是否被锁定"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """锁定账户"""
        self.locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock_account(self):
        """解锁账户"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['locked_until', 'failed_login_attempts'])
    
    def record_failed_login(self):
        """记录登录失败"""
        self.failed_login_attempts += 1
        
        # 如果失败次数过多，锁定账户
        if self.failed_login_attempts >= 5:
            self.lock_account()
        
        self.save(update_fields=['failed_login_attempts'])
    
    def record_successful_login(self, ip_address=None):
        """记录成功登录"""
        self.last_login = timezone.now()
        self.last_activity = timezone.now()
        self.failed_login_attempts = 0
        
        if ip_address:
            self.last_login_ip = ip_address
        
        self.save(update_fields=['last_login', 'last_activity', 'failed_login_attempts', 'last_login_ip'])
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def get_display_name(self):
        """获取显示名称"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    def can_manage_user(self, target_user):
        """检查是否可以管理目标用户"""
        # 不能管理自己
        if self.id == target_user.id:
            return False
        
        # 超级用户可以管理所有用户
        if self.is_superuser:
            return True
        
        # 只能管理同租户的用户
        if self.tenant_id != target_user.tenant_id:
            return False
        
        # 租户管理员可以管理租户内的所有用户
        if self.is_tenant_admin:
            return True
        
        # 检查用户管理权限
        return self.has_permission('user.edit_user')


class UserRole(models.Model):
    """
    用户角色关联模型 - 记录用户角色分配的详细信息
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, verbose_name='角色')
    
    # 分配信息
    assigned_at = models.DateTimeField('分配时间', auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='分配者',
        related_name='assigned_roles'
    )
    
    # 有效期
    expires_at = models.DateTimeField('过期时间', null=True, blank=True)
    is_active = models.BooleanField('是否激活', default=True)
    
    class Meta:
        db_table = 'users_user_role'
        verbose_name = '用户角色'
        verbose_name_plural = '用户角色'
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    def is_expired(self):
        """检查角色是否已过期"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    def is_valid(self):
        """检查角色分配是否有效"""
        return self.is_active and not self.is_expired()


class UserProfile(TenantModel):
    """
    用户配置文件 - 存储用户的个性化设置
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='用户',
        related_name='profile'
    )
    
    # 个人信息
    real_name = models.CharField('真实姓名', max_length=50, blank=True)
    id_number = models.CharField('身份证号', max_length=20, blank=True)
    birth_date = models.DateField('出生日期', null=True, blank=True)
    
    # 联系信息
    address = models.TextField('地址', blank=True)
    emergency_contact = models.CharField('紧急联系人', max_length=50, blank=True)
    emergency_phone = models.CharField('紧急联系电话', max_length=20, blank=True)
    
    # 交易设置
    default_risk_level = models.CharField(
        '默认风险等级',
        max_length=10,
        choices=[
            ('low', '低风险'),
            ('medium', '中风险'),
            ('high', '高风险'),
        ],
        default='medium'
    )
    
    # 通知设置
    email_notifications = models.BooleanField('邮件通知', default=True)
    sms_notifications = models.BooleanField('短信通知', default=False)
    push_notifications = models.BooleanField('推送通知', default=True)
    
    # 界面设置
    theme = models.CharField(
        '主题',
        max_length=10,
        choices=[
            ('light', '浅色'),
            ('dark', '深色'),
            ('auto', '自动'),
        ],
        default='light'
    )
    
    # 其他设置
    settings = models.JSONField('其他设置', default=dict, blank=True)
    
    class Meta:
        db_table = 'users_user_profile'
        verbose_name = '用户配置'
        verbose_name_plural = '用户配置'
    
    def __str__(self):
        return f"{self.user.username} 的配置"


class UserSession(models.Model):
    """
    用户会话模型 - 跟踪用户登录会话
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    session_key = models.CharField('会话键', max_length=40, unique=True)
    
    # 会话信息
    ip_address = models.GenericIPAddressField('IP地址')
    user_agent = models.TextField('用户代理')
    device_info = models.JSONField('设备信息', default=dict, blank=True)
    
    # 时间信息
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    last_activity = models.DateTimeField('最后活动', auto_now=True)
    expires_at = models.DateTimeField('过期时间')
    
    # 状态
    is_active = models.BooleanField('是否激活', default=True)
    
    class Meta:
        db_table = 'users_user_session'
        verbose_name = '用户会话'
        verbose_name_plural = '用户会话'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"
    
    def is_expired(self):
        """检查会话是否已过期"""
        return timezone.now() > self.expires_at
    
    def extend_session(self, duration_hours=24):
        """延长会话时间"""
        self.expires_at = timezone.now() + timezone.timedelta(hours=duration_hours)
        self.save(update_fields=['expires_at'])


class LoginLog(models.Model):
    """
    登录日志模型 - 记录用户登录历史
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='用户'
    )
    username = models.CharField('用户名', max_length=150)
    
    # 登录信息
    ip_address = models.GenericIPAddressField('IP地址')
    user_agent = models.TextField('用户代理')
    
    # 登录结果
    LOGIN_RESULT_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('blocked', '被阻止'),
    ]
    result = models.CharField('登录结果', max_length=10, choices=LOGIN_RESULT_CHOICES)
    failure_reason = models.CharField('失败原因', max_length=100, blank=True)
    
    # 时间信息
    attempted_at = models.DateTimeField('尝试时间', auto_now_add=True)
    
    class Meta:
        db_table = 'users_login_log'
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-attempted_at']
        indexes = [
            models.Index(fields=['user', '-attempted_at']),
            models.Index(fields=['ip_address', '-attempted_at']),
        ]
    
    def __str__(self):
        return f"{self.username} - {self.result} - {self.attempted_at}"