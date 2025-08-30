"""
用户管理服务
"""
import logging
from typing import Optional, List, Dict, Any
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.core.models import Tenant, Role
from apps.core.utils import TenantContext, create_default_roles
from .models import User, UserProfile, UserSession, LoginLog

logger = logging.getLogger(__name__)


class UserManagementService:
    """
    用户管理服务 - 提供用户创建、编辑、删除等功能
    """
    
    @staticmethod
    def create_user(
        tenant: Tenant,
        username: str,
        email: str,
        password: str,
        first_name: str = '',
        last_name: str = '',
        phone: str = '',
        roles: List[str] = None,
        is_tenant_admin: bool = False,
        created_by: Optional[User] = None
    ) -> User:
        """
        创建用户
        
        Args:
            tenant: 租户对象
            username: 用户名
            email: 邮箱
            password: 密码
            first_name: 名
            last_name: 姓
            phone: 手机号
            roles: 角色列表
            is_tenant_admin: 是否为租户管理员
            created_by: 创建者
        
        Returns:
            创建的用户对象
        """
        with TenantContext(tenant):
            # 验证租户是否可以添加用户
            if not tenant.can_add_user():
                raise ValidationError(f'租户用户数量已达到上限 ({tenant.max_users})')
            
            # 检查用户名是否已存在
            if User.objects.filter(tenant=tenant, username=username).exists():
                raise ValidationError(f'用户名 {username} 在此租户中已存在')
            
            # 检查邮箱是否已存在
            if email and User.objects.filter(tenant=tenant, email=email).exists():
                raise ValidationError(f'邮箱 {email} 在此租户中已存在')
            
            try:
                with transaction.atomic():
                    # 创建用户
                    user = User.objects.create(
                        tenant=tenant,
                        username=username,
                        email=email,
                        password=make_password(password),
                        first_name=first_name,
                        last_name=last_name,
                        phone=phone,
                        is_tenant_admin=is_tenant_admin,
                        is_active=True
                    )
                    
                    # 创建用户配置文件
                    UserProfile.objects.create(
                        user=user,
                        tenant=tenant
                    )
                    
                    # 分配角色
                    if roles:
                        for role_name in roles:
                            try:
                                role = Role.objects.get(name=role_name, tenant=tenant)
                                user.add_role(role)
                            except Role.DoesNotExist:
                                logger.warning(f'角色 {role_name} 不存在，跳过分配')
                    
                    # 如果没有指定角色且不是租户管理员，分配默认角色
                    if not roles and not is_tenant_admin:
                        try:
                            default_role = Role.objects.get(name='观察者', tenant=tenant)
                            user.add_role(default_role)
                        except Role.DoesNotExist:
                            logger.warning('默认角色"观察者"不存在')
                    
                    logger.info(f'用户创建成功: {username} (租户: {tenant.name})')
                    return user
            
            except Exception as e:
                logger.error(f'创建用户失败: {str(e)}', exc_info=True)
                raise ValidationError(f'创建用户失败: {str(e)}')
    
    @staticmethod
    def update_user(
        user: User,
        **kwargs
    ) -> User:
        """
        更新用户信息
        
        Args:
            user: 用户对象
            **kwargs: 要更新的字段
        
        Returns:
            更新后的用户对象
        """
        try:
            with transaction.atomic():
                # 更新基本信息
                for field, value in kwargs.items():
                    if hasattr(user, field):
                        if field == 'password' and value:
                            # 密码需要加密
                            setattr(user, field, make_password(value))
                        else:
                            setattr(user, field, value)
                
                user.save()
                
                # 更新角色
                if 'roles' in kwargs:
                    roles = kwargs['roles']
                    # 清除现有角色
                    user.roles.clear()
                    # 添加新角色
                    for role_name in roles:
                        try:
                            role = Role.objects.get(name=role_name, tenant=user.tenant)
                            user.add_role(role)
                        except Role.DoesNotExist:
                            logger.warning(f'角色 {role_name} 不存在，跳过分配')
                
                logger.info(f'用户更新成功: {user.username}')
                return user
        
        except Exception as e:
            logger.error(f'更新用户失败: {str(e)}', exc_info=True)
            raise ValidationError(f'更新用户失败: {str(e)}')
    
    @staticmethod
    def delete_user(user: User, deleted_by: Optional[User] = None) -> bool:
        """
        删除用户（软删除）
        
        Args:
            user: 要删除的用户
            deleted_by: 删除者
        
        Returns:
            是否删除成功
        """
        try:
            with transaction.atomic():
                # 软删除：设置为非激活状态
                user.is_active = False
                user.save()
                
                # 清除用户会话
                UserSession.objects.filter(user=user).update(is_active=False)
                
                logger.info(f'用户删除成功: {user.username} (删除者: {deleted_by})')
                return True
        
        except Exception as e:
            logger.error(f'删除用户失败: {str(e)}', exc_info=True)
            return False
    
    @staticmethod
    def get_user_list(
        tenant: Tenant,
        search: str = '',
        role_filter: str = '',
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取用户列表
        
        Args:
            tenant: 租户
            search: 搜索关键词
            role_filter: 角色过滤
            is_active: 是否激活
            page: 页码
            page_size: 每页大小
        
        Returns:
            用户列表和分页信息
        """
        with TenantContext(tenant):
            queryset = User.objects.filter(tenant=tenant)
            
            # 搜索过滤
            if search:
                queryset = queryset.filter(
                    models.Q(username__icontains=search) |
                    models.Q(email__icontains=search) |
                    models.Q(first_name__icontains=search) |
                    models.Q(last_name__icontains=search)
                )
            
            # 角色过滤
            if role_filter:
                queryset = queryset.filter(roles__name=role_filter)
            
            # 激活状态过滤
            if is_active is not None:
                queryset = queryset.filter(is_active=is_active)
            
            # 排序
            queryset = queryset.order_by('-date_joined')
            
            # 分页
            total = queryset.count()
            start = (page - 1) * page_size
            end = start + page_size
            users = queryset[start:end]
            
            return {
                'users': users,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }


class AuthenticationService:
    """
    认证服务 - 处理用户登录、登出等认证相关功能
    """
    
    @staticmethod
    def authenticate_user(
        username: str,
        password: str,
        tenant: Optional[Tenant] = None,
        ip_address: str = '',
        user_agent: str = ''
    ) -> Optional[User]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            tenant: 租户（可选）
            ip_address: IP地址
            user_agent: 用户代理
        
        Returns:
            认证成功的用户对象，失败返回None
        """
        try:
            # 记录登录尝试
            login_log = LoginLog.objects.create(
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                result='failed'  # 默认失败，成功时会更新
            )
            
            # 查找用户
            user_query = User.objects.filter(username=username, is_active=True)
            if tenant:
                user_query = user_query.filter(tenant=tenant)
            
            user = user_query.first()
            
            if not user:
                login_log.failure_reason = '用户不存在'
                login_log.save()
                logger.warning(f'登录失败: 用户 {username} 不存在')
                return None
            
            # 检查账户是否被锁定
            if user.is_account_locked():
                login_log.user = user
                login_log.result = 'blocked'
                login_log.failure_reason = '账户被锁定'
                login_log.save()
                logger.warning(f'登录失败: 用户 {username} 账户被锁定')
                return None
            
            # 验证密码
            if not user.check_password(password):
                user.record_failed_login()
                login_log.user = user
                login_log.failure_reason = '密码错误'
                login_log.save()
                logger.warning(f'登录失败: 用户 {username} 密码错误')
                return None
            
            # 验证租户状态
            if not user.tenant.is_active:
                login_log.user = user
                login_log.result = 'blocked'
                login_log.failure_reason = '租户已禁用'
                login_log.save()
                logger.warning(f'登录失败: 租户 {user.tenant.name} 已禁用')
                return None
            
            # 验证租户订阅
            if not user.tenant.is_subscription_active():
                login_log.user = user
                login_log.result = 'blocked'
                login_log.failure_reason = '租户订阅已过期'
                login_log.save()
                logger.warning(f'登录失败: 租户 {user.tenant.name} 订阅已过期')
                return None
            
            # 登录成功
            user.record_successful_login(ip_address)
            login_log.user = user
            login_log.result = 'success'
            login_log.save()
            
            logger.info(f'用户登录成功: {username} (租户: {user.tenant.name})')
            return user
        
        except Exception as e:
            logger.error(f'用户认证异常: {str(e)}', exc_info=True)
            return None
    
    @staticmethod
    def create_user_session(
        user: User,
        session_key: str,
        ip_address: str,
        user_agent: str,
        device_info: Dict = None
    ) -> UserSession:
        """
        创建用户会话
        
        Args:
            user: 用户对象
            session_key: 会话键
            ip_address: IP地址
            user_agent: 用户代理
            device_info: 设备信息
        
        Returns:
            用户会话对象
        """
        # 清理过期会话
        UserSession.objects.filter(
            user=user,
            expires_at__lt=timezone.now()
        ).delete()
        
        # 创建新会话
        session = UserSession.objects.create(
            user=user,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info or {},
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        return session
    
    @staticmethod
    def logout_user(user: User, session_key: str = None):
        """
        用户登出
        
        Args:
            user: 用户对象
            session_key: 会话键（可选，如果提供则只登出指定会话）
        """
        try:
            if session_key:
                # 登出指定会话
                UserSession.objects.filter(
                    user=user,
                    session_key=session_key
                ).update(is_active=False)
            else:
                # 登出所有会话
                UserSession.objects.filter(user=user).update(is_active=False)
            
            logger.info(f'用户登出: {user.username}')
        
        except Exception as e:
            logger.error(f'用户登出异常: {str(e)}', exc_info=True)


class TenantManagementService:
    """
    租户管理服务
    """
    
    @staticmethod
    def create_tenant(
        name: str,
        schema_name: str,
        domain: str = '',
        max_users: int = 100,
        max_strategies: int = 50,
        max_exchange_accounts: int = 10
    ) -> Tenant:
        """
        创建租户
        
        Args:
            name: 租户名称
            schema_name: 数据库模式名
            domain: 域名
            max_users: 最大用户数
            max_strategies: 最大策略数
            max_exchange_accounts: 最大交易所账户数
        
        Returns:
            创建的租户对象
        """
        try:
            with transaction.atomic():
                # 创建租户
                tenant = Tenant.objects.create(
                    name=name,
                    schema_name=schema_name,
                    domain=domain,
                    max_users=max_users,
                    max_strategies=max_strategies,
                    max_exchange_accounts=max_exchange_accounts
                )
                
                # 创建默认角色
                create_default_roles(tenant)
                
                logger.info(f'租户创建成功: {name}')
                return tenant
        
        except Exception as e:
            logger.error(f'创建租户失败: {str(e)}', exc_info=True)
            raise ValidationError(f'创建租户失败: {str(e)}')
    
    @staticmethod
    def setup_tenant_admin(
        tenant: Tenant,
        username: str,
        email: str,
        password: str,
        first_name: str = '',
        last_name: str = ''
    ) -> User:
        """
        为租户设置管理员
        
        Args:
            tenant: 租户对象
            username: 管理员用户名
            email: 管理员邮箱
            password: 管理员密码
            first_name: 名
            last_name: 姓
        
        Returns:
            创建的管理员用户
        """
        admin_user = UserManagementService.create_user(
            tenant=tenant,
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            roles=['超级管理员'],
            is_tenant_admin=True
        )
        
        logger.info(f'租户管理员设置成功: {username} (租户: {tenant.name})')
        return admin_user