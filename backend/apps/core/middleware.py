"""
多租户中间件
"""
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from .models import Tenant
from .utils import set_current_tenant, clear_current_tenant, get_tenant_by_domain

logger = logging.getLogger(__name__)
User = get_user_model()


class TenantMiddleware(MiddlewareMixin):
    """
    租户中间件 - 负责识别和设置当前请求的租户上下文
    
    租户识别优先级：
    1. HTTP头部 X-Tenant-ID
    2. 用户所属租户（如果已认证）
    3. 域名映射
    4. 默认租户（如果配置）
    """
    
    def process_request(self, request):
        """处理请求，设置租户上下文"""
        tenant = None
        
        try:
            # 1. 尝试从HTTP头部获取租户ID
            tenant_id = request.META.get('HTTP_X_TENANT_ID')
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id, is_active=True)
                    logger.debug(f"从HTTP头部识别租户: {tenant.name}")
                except Tenant.DoesNotExist:
                    logger.warning(f"HTTP头部指定的租户不存在: {tenant_id}")
            
            # 2. 如果没有从头部获取到，尝试从用户获取
            if not tenant and hasattr(request, 'user') and request.user.is_authenticated:
                if hasattr(request.user, 'tenant'):
                    tenant = request.user.tenant
                    logger.debug(f"从用户获取租户: {tenant.name}")
            
            # 3. 尝试从域名映射获取租户
            if not tenant:
                host = request.get_host()
                # 移除端口号
                domain = host.split(':')[0]
                tenant = get_tenant_by_domain(domain)
                if tenant:
                    logger.debug(f"从域名映射获取租户: {tenant.name} (域名: {domain})")
            
            # 4. 如果仍然没有租户，检查是否是管理员路径
            if not tenant:
                path = request.path_info
                # 管理员路径不需要租户上下文
                if path.startswith('/admin/') or path.startswith('/api/admin/'):
                    logger.debug("管理员路径，跳过租户设置")
                    return None
                
                # 健康检查等系统路径
                if path in ['/health/', '/metrics/', '/api/health/']:
                    logger.debug("系统路径，跳过租户设置")
                    return None
            
            # 设置租户上下文
            if tenant:
                # 验证租户是否激活
                if not tenant.is_active:
                    logger.warning(f"租户已被禁用: {tenant.name}")
                    return JsonResponse({
                        'error': '租户已被禁用',
                        'code': 'TENANT_DISABLED'
                    }, status=403)
                
                # 验证租户订阅是否有效
                if not tenant.is_subscription_active():
                    logger.warning(f"租户订阅已过期: {tenant.name}")
                    return JsonResponse({
                        'error': '租户订阅已过期',
                        'code': 'SUBSCRIPTION_EXPIRED'
                    }, status=403)
                
                set_current_tenant(tenant)
                request.tenant = tenant
                logger.debug(f"设置当前租户: {tenant.name}")
            else:
                # 对于需要租户上下文的API路径，返回错误
                # 但排除不需要租户上下文的路径
                skip_tenant_paths = [
                    '/api/admin/',
                    '/api/users/auth/login/',
                    '/api/users/auth/refresh/',
                    '/api/health/',
                ]
                
                needs_tenant = (
                    request.path_info.startswith('/api/') and 
                    not any(request.path_info.startswith(path) for path in skip_tenant_paths)
                )
                
                if needs_tenant:
                    logger.warning(f"API请求缺少租户上下文: {request.path_info}")
                    return JsonResponse({
                        'error': '无法确定租户上下文',
                        'code': 'TENANT_REQUIRED'
                    }, status=400)
        
        except Exception as e:
            logger.error(f"租户中间件处理异常: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': '租户上下文处理失败',
                'code': 'TENANT_ERROR'
            }, status=500)
        
        return None
    
    def process_response(self, request, response):
        """处理响应，清理租户上下文"""
        try:
            # 清除租户上下文
            clear_current_tenant()
            
            # 在响应头中添加租户信息（用于调试）
            if hasattr(request, 'tenant') and request.tenant:
                response['X-Tenant-Name'] = request.tenant.name
                response['X-Tenant-ID'] = str(request.tenant.id)
        
        except Exception as e:
            logger.error(f"清理租户上下文异常: {str(e)}", exc_info=True)
        
        return response
    
    def process_exception(self, request, exception):
        """处理异常，确保清理租户上下文"""
        try:
            clear_current_tenant()
        except Exception as e:
            logger.error(f"异常处理中清理租户上下文失败: {str(e)}", exc_info=True)
        
        return None


class TenantAccessControlMiddleware(MiddlewareMixin):
    """
    租户访问控制中间件 - 确保用户只能访问自己租户的数据
    """
    
    def process_request(self, request):
        """验证用户的租户访问权限"""
        # 跳过不需要验证的路径
        skip_paths = [
            '/admin/',
            '/api/admin/',
            '/health/',
            '/metrics/',
            '/api/health/',
            '/api/auth/login/',
            '/api/auth/logout/',
        ]
        
        if any(request.path_info.startswith(path) for path in skip_paths):
            return None
        
        # 只对已认证用户进行验证
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # 超级用户跳过验证
        if request.user.is_superuser:
            return None
        
        # 验证用户租户与当前租户是否匹配
        if hasattr(request, 'tenant') and hasattr(request.user, 'tenant'):
            if request.tenant.id != request.user.tenant.id:
                logger.warning(
                    f"用户 {request.user.username} 尝试访问其他租户 {request.tenant.name} 的数据"
                )
                return JsonResponse({
                    'error': '无权限访问此租户的数据',
                    'code': 'TENANT_ACCESS_DENIED'
                }, status=403)
        
        return None


class TenantSecurityMiddleware(MiddlewareMixin):
    """
    租户安全中间件 - 记录安全相关的操作和异常访问
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('security')
    
    def __call__(self, request):
        # 记录敏感操作
        self._log_sensitive_operations(request)
        
        response = self.get_response(request)
        
        # 记录访问日志
        self._log_access(request, response)
        
        return response
    
    def _log_sensitive_operations(self, request):
        """记录敏感操作"""
        sensitive_paths = [
            '/api/users/',
            '/api/roles/',
            '/api/permissions/',
            '/api/exchanges/',
            '/api/orders/',
        ]
        
        if any(request.path_info.startswith(path) for path in sensitive_paths):
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                self.security_logger.info(
                    f"敏感操作: 用户={getattr(request.user, 'username', 'anonymous')}, "
                    f"方法={request.method}, 路径={request.path_info}, "
                    f"IP={self._get_client_ip(request)}, "
                    f"租户={getattr(request, 'tenant', None)}"
                )
    
    def _log_access(self, request, response):
        """记录访问日志"""
        # 只记录API访问
        if request.path_info.startswith('/api/'):
            log_data = {
                'user': getattr(request.user, 'username', 'anonymous'),
                'method': request.method,
                'path': request.path_info,
                'status': response.status_code,
                'ip': self._get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'tenant': str(getattr(request, 'tenant', None)),
            }
            
            # 根据状态码选择日志级别
            if response.status_code >= 400:
                self.security_logger.warning(f"API访问异常: {log_data}")
            else:
                self.security_logger.info(f"API访问: {log_data}")
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class TenantCacheMiddleware(MiddlewareMixin):
    """
    租户缓存中间件 - 为缓存添加租户前缀
    """
    
    def process_request(self, request):
        """在请求处理前设置缓存前缀"""
        if hasattr(request, 'tenant') and request.tenant:
            # 这里可以设置缓存前缀，具体实现取决于缓存后端
            pass
        
        return None