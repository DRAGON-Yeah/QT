"""
JWT认证模块 - 提供JWT token生成、验证和用户认证功能
"""
import jwt
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserSession, LoginLog
from apps.core.utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)


class JWTService:
    """JWT服务类 - 处理JWT token的生成和验证"""
    
    @staticmethod
    def generate_tokens(user, request=None):
        """
        生成JWT访问令牌和刷新令牌
        
        Args:
            user: 用户对象
            request: HTTP请求对象（可选）
        
        Returns:
            dict: 包含access_token和refresh_token的字典
        """
        try:
            # 使用django-rest-framework-simplejwt生成token
            refresh = RefreshToken.for_user(user)
            
            # 添加自定义声明
            refresh['tenant_id'] = str(user.tenant.id) if user.tenant else None
            refresh['username'] = user.username
            refresh['is_tenant_admin'] = user.is_tenant_admin
            refresh['roles'] = [role.name for role in user.roles.filter(is_active=True)]
            refresh['permissions'] = list(user.get_all_permissions())
            
            # 获取访问令牌
            access_token = refresh.access_token
            
            # 记录用户会话
            if request:
                ip_address = get_client_ip(request)
                user_agent = get_user_agent(request)
                
                # 创建用户会话记录
                UserSession.objects.create(
                    user=user,
                    session_key=str(access_token),
                    ip_address=ip_address,
                    user_agent=user_agent,
                    expires_at=timezone.now() + timedelta(hours=24)
                )
                
                # 更新用户登录信息
                user.record_successful_login(ip_address)
            
            return {
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'token_type': 'Bearer',
                'expires_in': settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(hours=1)).total_seconds(),
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'tenant_id': str(user.tenant.id) if user.tenant else None,
                    'tenant_name': user.tenant.name if user.tenant else None,
                    'is_tenant_admin': user.is_tenant_admin,
                    'roles': [role.name for role in user.roles.filter(is_active=True)],
                    'permissions': list(user.get_all_permissions()),
                }
            }
        except Exception as e:
            logger.error(f"生成JWT token失败: {e}")
            raise exceptions.AuthenticationFailed('Token生成失败')
    
    @staticmethod
    def verify_token(token):
        """
        验证JWT token
        
        Args:
            token: JWT token字符串
        
        Returns:
            dict: token载荷数据
        
        Raises:
            AuthenticationFailed: token无效时抛出异常
        """
        try:
            # 使用django-rest-framework-simplejwt验证token
            from rest_framework_simplejwt.tokens import UntypedToken
            UntypedToken(token)
            
            # 解码token获取载荷
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=['HS256'],
                options={'verify_signature': False}  # simplejwt已经验证过签名
            )
            
            return payload
        except (jwt.ExpiredSignatureError, TokenError):
            raise exceptions.AuthenticationFailed('Token已过期')
        except (jwt.InvalidTokenError, InvalidToken):
            raise exceptions.AuthenticationFailed('无效的Token')
        except Exception as e:
            logger.error(f"验证JWT token失败: {e}")
            raise exceptions.AuthenticationFailed('Token验证失败')
    
    @staticmethod
    def refresh_token(refresh_token):
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            dict: 新的访问令牌信息
        """
        try:
            refresh = RefreshToken(refresh_token)
            access_token = refresh.access_token
            
            return {
                'access_token': str(access_token),
                'token_type': 'Bearer',
                'expires_in': settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', timedelta(hours=1)).total_seconds(),
            }
        except TokenError:
            raise exceptions.AuthenticationFailed('刷新令牌无效或已过期')
    
    @staticmethod
    def revoke_token(token):
        """
        撤销token（将token加入黑名单）
        
        Args:
            token: 要撤销的token
        """
        try:
            refresh = RefreshToken(token)
            refresh.blacklist()
        except Exception as e:
            logger.error(f"撤销token失败: {e}")


class CustomJWTAuthentication(JWTAuthentication):
    """
    自定义JWT认证类 - 扩展django-rest-framework-simplejwt的认证功能
    """
    
    def authenticate(self, request):
        """
        认证用户
        
        Args:
            request: HTTP请求对象
        
        Returns:
            tuple: (user, token) 或 None
        """
        header = self.get_header(request)
        if header is None:
            return None
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None
        
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        
        # 检查用户状态
        if not user.is_active:
            raise exceptions.AuthenticationFailed('用户账户已被禁用')
        
        # 检查账户是否被锁定
        if user.is_account_locked():
            raise exceptions.AuthenticationFailed('账户已被锁定，请稍后再试')
        
        # 检查租户状态
        if user.tenant and not user.tenant.is_active:
            raise exceptions.AuthenticationFailed('租户账户已被禁用')
        
        # 更新用户活动时间
        user.update_activity()
        
        # 验证会话是否有效
        self.validate_session(user, str(validated_token))
        
        return (user, validated_token)
    
    def validate_session(self, user, token):
        """
        验证用户会话
        
        Args:
            user: 用户对象
            token: token字符串
        """
        try:
            session = UserSession.objects.get(
                user=user,
                session_key=token,
                is_active=True
            )
            
            # 检查会话是否过期
            if session.is_expired():
                session.is_active = False
                session.save()
                raise exceptions.AuthenticationFailed('会话已过期，请重新登录')
            
            # 更新会话活动时间
            session.last_activity = timezone.now()
            session.save(update_fields=['last_activity'])
            
        except UserSession.DoesNotExist:
            # 如果找不到会话记录，可能是旧的token，允许通过但记录警告
            logger.warning(f"用户 {user.username} 使用了没有会话记录的token")


class LoginService:
    """登录服务类 - 处理用户登录逻辑"""
    
    @staticmethod
    def authenticate_user(username, password, request=None):
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            request: HTTP请求对象（可选）
        
        Returns:
            dict: 认证结果和token信息
        
        Raises:
            AuthenticationFailed: 认证失败时抛出异常
        """
        ip_address = get_client_ip(request) if request else None
        user_agent = get_user_agent(request) if request else None
        
        # 记录登录尝试
        login_log = LoginLog.objects.create(
            username=username,
            ip_address=ip_address or '0.0.0.0',
            user_agent=user_agent or '',
            result='failed',  # 默认为失败，成功时会更新
        )
        
        try:
            # 尝试获取用户
            try:
                user = User.objects.get(username=username)
                login_log.user = user
                login_log.save()
            except User.DoesNotExist:
                login_log.failure_reason = '用户不存在'
                login_log.save()
                raise exceptions.AuthenticationFailed('用户名或密码错误')
            
            # 检查账户是否被锁定
            if user.is_account_locked():
                login_log.result = 'blocked'
                login_log.failure_reason = '账户已被锁定'
                login_log.save()
                raise exceptions.AuthenticationFailed('账户已被锁定，请稍后再试')
            
            # 检查用户是否激活
            if not user.is_active:
                login_log.failure_reason = '账户已被禁用'
                login_log.save()
                raise exceptions.AuthenticationFailed('账户已被禁用')
            
            # 检查租户是否激活
            if user.tenant and not user.tenant.is_active:
                login_log.failure_reason = '租户已被禁用'
                login_log.save()
                raise exceptions.AuthenticationFailed('租户账户已被禁用')
            
            # 验证密码
            if not user.check_password(password):
                user.record_failed_login()
                login_log.failure_reason = '密码错误'
                login_log.save()
                raise exceptions.AuthenticationFailed('用户名或密码错误')
            
            # 认证成功，生成token
            tokens = JWTService.generate_tokens(user, request)
            
            # 更新登录日志
            login_log.result = 'success'
            login_log.failure_reason = ''
            login_log.save()
            
            logger.info(f"用户 {username} 登录成功，IP: {ip_address}")
            
            return tokens
            
        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            login_log.failure_reason = f'系统错误: {str(e)}'
            login_log.save()
            logger.error(f"用户 {username} 登录失败: {e}")
            raise exceptions.AuthenticationFailed('登录失败，请稍后再试')
    
    @staticmethod
    def logout_user(user, token=None):
        """
        用户登出
        
        Args:
            user: 用户对象
            token: 访问令牌（可选）
        """
        try:
            # 撤销token
            if token:
                JWTService.revoke_token(token)
            
            # 标记会话为非活跃
            if token:
                UserSession.objects.filter(
                    user=user,
                    session_key=token
                ).update(is_active=False)
            
            logger.info(f"用户 {user.username} 登出成功")
            
        except Exception as e:
            logger.error(f"用户 {user.username} 登出失败: {e}")
    
    @staticmethod
    def logout_all_sessions(user):
        """
        登出用户的所有会话
        
        Args:
            user: 用户对象
        """
        try:
            # 标记所有会话为非活跃
            UserSession.objects.filter(user=user).update(is_active=False)
            
            logger.info(f"用户 {user.username} 的所有会话已登出")
            
        except Exception as e:
            logger.error(f"登出用户 {user.username} 的所有会话失败: {e}")


class PasswordService:
    """密码服务类 - 处理密码相关操作"""
    
    @staticmethod
    def validate_password_strength(password):
        """
        验证密码强度
        
        Args:
            password: 密码字符串
        
        Returns:
            tuple: (is_valid, message)
        """
        if len(password) < 8:
            return False, "密码长度至少8位"
        
        if not any(c.isupper() for c in password):
            return False, "密码必须包含大写字母"
        
        if not any(c.islower() for c in password):
            return False, "密码必须包含小写字母"
        
        if not any(c.isdigit() for c in password):
            return False, "密码必须包含数字"
        
        # 检查特殊字符
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "密码必须包含特殊字符"
        
        return True, "密码强度符合要求"
    
    @staticmethod
    def change_password(user, old_password, new_password):
        """
        修改密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            bool: 是否修改成功
        
        Raises:
            AuthenticationFailed: 密码验证失败时抛出异常
        """
        # 验证旧密码
        if not user.check_password(old_password):
            raise exceptions.AuthenticationFailed('原密码错误')
        
        # 验证新密码强度
        is_valid, message = PasswordService.validate_password_strength(new_password)
        if not is_valid:
            raise exceptions.ValidationError(message)
        
        # 检查新密码是否与旧密码相同
        if user.check_password(new_password):
            raise exceptions.ValidationError('新密码不能与原密码相同')
        
        # 设置新密码
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.save()
        
        # 登出所有会话，强制重新登录
        LoginService.logout_all_sessions(user)
        
        logger.info(f"用户 {user.username} 修改密码成功")
        return True
    
    @staticmethod
    def reset_password(user, new_password):
        """
        重置密码（管理员操作）
        
        Args:
            user: 用户对象
            new_password: 新密码
        
        Returns:
            bool: 是否重置成功
        """
        # 验证新密码强度
        is_valid, message = PasswordService.validate_password_strength(new_password)
        if not is_valid:
            raise exceptions.ValidationError(message)
        
        # 设置新密码
        user.set_password(new_password)
        user.password_changed_at = timezone.now()
        user.save()
        
        # 登出所有会话
        LoginService.logout_all_sessions(user)
        
        logger.info(f"管理员重置用户 {user.username} 的密码")
        return True


class SessionService:
    """会话服务类 - 管理用户会话"""
    
    @staticmethod
    def get_active_sessions(user):
        """
        获取用户的活跃会话
        
        Args:
            user: 用户对象
        
        Returns:
            QuerySet: 活跃会话查询集
        """
        return UserSession.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).order_by('-last_activity')
    
    @staticmethod
    def terminate_session(user, session_id):
        """
        终止指定会话
        
        Args:
            user: 用户对象
            session_id: 会话ID
        
        Returns:
            bool: 是否终止成功
        """
        try:
            session = UserSession.objects.get(
                id=session_id,
                user=user,
                is_active=True
            )
            session.is_active = False
            session.save()
            
            logger.info(f"用户 {user.username} 的会话 {session_id} 已终止")
            return True
        except UserSession.DoesNotExist:
            return False
    
    @staticmethod
    def cleanup_expired_sessions():
        """清理过期会话"""
        expired_count = UserSession.objects.filter(
            expires_at__lt=timezone.now()
        ).update(is_active=False)
        
        logger.info(f"清理了 {expired_count} 个过期会话")
        return expired_count


# 导出主要的认证类和服务
__all__ = [
    'JWTService',
    'CustomJWTAuthentication', 
    'LoginService',
    'PasswordService',
    'SessionService'
]