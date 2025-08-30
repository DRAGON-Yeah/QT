"""
用户管理视图
"""
import logging
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from apps.core.permissions import TenantPermission, require_permission
from apps.core.models import Role, Permission
from apps.core.utils import TenantContext
from .models import User, UserProfile, UserRole, LoginLog, UserSession
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserPasswordChangeSerializer, RoleSerializer, PermissionSerializer,
    RoleAssignmentSerializer, UserRoleSerializer, LoginSerializer,
    PasswordChangeSerializer, PasswordResetSerializer
)
from .services import UserManagementService
from .authentication import LoginService, JWTService, PasswordService, SessionService

logger = logging.getLogger(__name__)


class UserManagementViewSet(ModelViewSet):
    """
    用户管理视图集
    提供用户的CRUD操作
    """
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """获取查询集"""
        return User.objects.filter(
            tenant=self.request.user.tenant
        ).select_related('tenant').prefetch_related('roles', 'profile')
    
    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        else:
            return UserDetailSerializer
    
    @require_permission('user.view_user')
    def list(self, request, *args, **kwargs):
        """获取用户列表"""
        queryset = self.get_queryset()
        
        # 搜索过滤
        search = request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search)
            )
        
        # 角色过滤
        role_filter = request.query_params.get('role', '')
        if role_filter:
            queryset = queryset.filter(roles__name=role_filter)
        
        # 状态过滤
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # 管理员过滤
        is_admin = request.query_params.get('is_admin')
        if is_admin is not None:
            queryset = queryset.filter(is_tenant_admin=is_admin.lower() == 'true')
        
        # 排序
        ordering = request.query_params.get('ordering', '-date_joined')
        queryset = queryset.order_by(ordering)
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @require_permission('user.view_user')
    def retrieve(self, request, *args, **kwargs):
        """获取用户详情"""
        return super().retrieve(request, *args, **kwargs)
    
    @require_permission('user.add_user')
    def create(self, request, *args, **kwargs):
        """创建用户"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            
            # 返回创建的用户详情
            detail_serializer = UserDetailSerializer(user)
            
            logger.info(f'用户创建成功: {user.username} (创建者: {request.user.username})')
            
            return Response(
                {
                    'success': True,
                    'message': '用户创建成功',
                    'data': detail_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f'创建用户失败: {str(e)}', exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': f'创建用户失败: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @require_permission('user.change_user')
    def update(self, request, *args, **kwargs):
        """更新用户"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # 检查是否有权限管理此用户
        if not request.user.can_manage_user(instance):
            return Response(
                {'success': False, 'message': '没有权限管理此用户'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            
            logger.info(f'用户更新成功: {user.username} (更新者: {request.user.username})')
            
            return Response(
                {
                    'success': True,
                    'message': '用户更新成功',
                    'data': serializer.data
                }
            )
        
        except Exception as e:
            logger.error(f'更新用户失败: {str(e)}', exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': f'更新用户失败: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @require_permission('user.change_user')
    def partial_update(self, request, *args, **kwargs):
        """部分更新用户"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @require_permission('user.delete_user')
    def destroy(self, request, *args, **kwargs):
        """删除用户（软删除）"""
        instance = self.get_object()
        
        # 检查是否有权限管理此用户
        if not request.user.can_manage_user(instance):
            return Response(
                {'success': False, 'message': '没有权限管理此用户'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不能删除自己
        if instance.id == request.user.id:
            return Response(
                {'success': False, 'message': '不能删除自己的账户'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            success = UserManagementService.delete_user(instance, request.user)
            
            if success:
                logger.info(f'用户删除成功: {instance.username} (删除者: {request.user.username})')
                return Response(
                    {
                        'success': True,
                        'message': '用户删除成功'
                    }
                )
            else:
                return Response(
                    {
                        'success': False,
                        'message': '用户删除失败'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f'删除用户失败: {str(e)}', exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': f'删除用户失败: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @require_permission('user.change_password')
    def change_password(self, request, pk=None):
        """修改用户密码"""
        user = self.get_object()
        
        # 检查是否有权限管理此用户
        if not request.user.can_manage_user(user) and user.id != request.user.id:
            return Response(
                {'success': False, 'message': '没有权限修改此用户密码'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = UserPasswordChangeSerializer(
            data=request.data,
            context={'user': user, 'request': request}
        )
        
        if serializer.is_valid():
            try:
                serializer.save()
                
                logger.info(f'密码修改成功: {user.username} (操作者: {request.user.username})')
                
                return Response(
                    {
                        'success': True,
                        'message': '密码修改成功'
                    }
                )
            
            except Exception as e:
                logger.error(f'修改密码失败: {str(e)}', exc_info=True)
                return Response(
                    {
                        'success': False,
                        'message': f'修改密码失败: {str(e)}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {
                'success': False,
                'message': '数据验证失败',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    @require_permission('user.change_user')
    def toggle_status(self, request, pk=None):
        """切换用户状态（激活/禁用）"""
        user = self.get_object()
        
        # 检查是否有权限管理此用户
        if not request.user.can_manage_user(user):
            return Response(
                {'success': False, 'message': '没有权限管理此用户'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 不能禁用自己
        if user.id == request.user.id:
            return Response(
                {'success': False, 'message': '不能禁用自己的账户'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user.is_active = not user.is_active
            user.save()
            
            action = '激活' if user.is_active else '禁用'
            logger.info(f'用户{action}成功: {user.username} (操作者: {request.user.username})')
            
            return Response(
                {
                    'success': True,
                    'message': f'用户{action}成功',
                    'data': {'is_active': user.is_active}
                }
            )
        
        except Exception as e:
            logger.error(f'切换用户状态失败: {str(e)}', exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': f'操作失败: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @require_permission('user.change_user')
    def unlock_account(self, request, pk=None):
        """解锁用户账户"""
        user = self.get_object()
        
        # 检查是否有权限管理此用户
        if not request.user.can_manage_user(user):
            return Response(
                {'success': False, 'message': '没有权限管理此用户'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user.unlock_account()
            
            logger.info(f'账户解锁成功: {user.username} (操作者: {request.user.username})')
            
            return Response(
                {
                    'success': True,
                    'message': '账户解锁成功'
                }
            )
        
        except Exception as e:
            logger.error(f'解锁账户失败: {str(e)}', exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': f'解锁失败: {str(e)}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    @require_permission('user.view_user')
    def statistics(self, request):
        """获取用户统计信息"""
        tenant = request.user.tenant
        
        with TenantContext(tenant):
            stats = {
                'total_users': User.objects.filter(tenant=tenant).count(),
                'active_users': User.objects.filter(tenant=tenant, is_active=True).count(),
                'admin_users': User.objects.filter(tenant=tenant, is_tenant_admin=True).count(),
                'locked_users': User.objects.filter(
                    tenant=tenant,
                    locked_until__gt=timezone.now()
                ).count(),
                'recent_logins': User.objects.filter(
                    tenant=tenant,
                    last_login__gte=timezone.now() - timezone.timedelta(days=7)
                ).count(),
                'role_distribution': list(
                    Role.objects.filter(tenant=tenant)
                    .annotate(user_count=Count('users'))
                    .values('name', 'user_count')
                )
            }
        
        return Response({
            'success': True,
            'data': stats
        })


class RoleManagementViewSet(ModelViewSet):
    """
    角色管理视图集
    """
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    def get_queryset(self):
        """获取查询集"""
        return Role.objects.filter(
            tenant=self.request.user.tenant
        ).prefetch_related('permissions')
    
    @require_permission('role.view_role')
    def list(self, request, *args, **kwargs):
        """获取角色列表"""
        return super().list(request, *args, **kwargs)
    
    @require_permission('role.view_role')
    def retrieve(self, request, *args, **kwargs):
        """获取角色详情"""
        return super().retrieve(request, *args, **kwargs)
    
    @require_permission('role.add_role')
    def create(self, request, *args, **kwargs):
        """创建角色"""
        return super().create(request, *args, **kwargs)
    
    @require_permission('role.change_role')
    def update(self, request, *args, **kwargs):
        """更新角色"""
        return super().update(request, *args, **kwargs)
    
    @require_permission('role.change_role')
    def partial_update(self, request, *args, **kwargs):
        """部分更新角色"""
        return super().partial_update(request, *args, **kwargs)
    
    @require_permission('role.delete_role')
    def destroy(self, request, *args, **kwargs):
        """删除角色"""
        instance = self.get_object()
        
        # 检查是否有用户使用此角色
        if instance.users.filter(is_active=True).exists():
            return Response(
                {
                    'success': False,
                    'message': '此角色正在被用户使用，无法删除'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)


class PermissionListView(APIView):
    """
    权限列表视图
    """
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    @require_permission('role.view_role')
    def get(self, request):
        """获取权限列表"""
        permissions = Permission.objects.all().order_by('category', 'name')
        
        # 按分类分组
        grouped_permissions = {}
        for permission in permissions:
            category = permission.get_category_display()
            if category not in grouped_permissions:
                grouped_permissions[category] = []
            
            grouped_permissions[category].append({
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename,
                'description': permission.description
            })
        
        return Response({
            'success': True,
            'data': grouped_permissions
        })


class RoleAssignmentView(APIView):
    """
    角色分配视图
    """
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    @require_permission('user.change_user')
    def post(self, request):
        """批量分配角色"""
        serializer = RoleAssignmentSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                results = serializer.save()
                
                logger.info(f'角色分配完成 (操作者: {request.user.username})')
                
                return Response(
                    {
                        'success': True,
                        'message': '角色分配完成',
                        'data': results
                    }
                )
            
            except Exception as e:
                logger.error(f'角色分配失败: {str(e)}', exc_info=True)
                return Response(
                    {
                        'success': False,
                        'message': f'角色分配失败: {str(e)}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(
            {
                'success': False,
                'message': '数据验证失败',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class UserLoginLogView(APIView):
    """
    用户登录日志视图
    """
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    @require_permission('user.view_user')
    def get(self, request, user_id=None):
        """获取登录日志"""
        if user_id:
            # 获取指定用户的登录日志
            try:
                user = User.objects.get(id=user_id, tenant=request.user.tenant)
                logs = LoginLog.objects.filter(user=user)
            except User.DoesNotExist:
                return Response(
                    {'success': False, 'message': '用户不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # 获取所有用户的登录日志
            logs = LoginLog.objects.filter(
                user__tenant=request.user.tenant
            ).select_related('user')
        
        # 过滤和排序
        result_filter = request.query_params.get('result')
        if result_filter:
            logs = logs.filter(result=result_filter)
        
        logs = logs.order_by('-attempted_at')
        
        # 分页
        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        total = logs.count()
        log_list = logs[start:end]
        
        data = []
        for log in log_list:
            data.append({
                'id': log.id,
                'username': log.username,
                'user_id': log.user.id if log.user else None,
                'ip_address': log.ip_address,
                'user_agent': log.user_agent,
                'result': log.result,
                'failure_reason': log.failure_reason,
                'attempted_at': log.attempted_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return Response({
            'success': True,
            'data': {
                'logs': data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
        })


class LoginView(APIView):
    """
    用户登录视图
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """用户登录"""
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            try:
                # 用户认证
                tokens = LoginService.authenticate_user(username, password, request)
                
                return Response({
                    'success': True,
                    'message': '登录成功',
                    'data': tokens
                })
            
            except Exception as e:
                logger.error(f'用户登录失败: {username} - {str(e)}')
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response({
            'success': False,
            'message': '数据验证失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    用户登出视图
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """用户登出"""
        try:
            # 获取当前token
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = None
            
            # 执行登出
            LoginService.logout_user(request.user, token)
            
            return Response({
                'success': True,
                'message': '登出成功'
            })
        
        except Exception as e:
            logger.error(f'用户登出失败: {request.user.username} - {str(e)}')
            return Response({
                'success': False,
                'message': '登出失败'
            }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAllView(APIView):
    """
    登出所有会话视图
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """登出所有会话"""
        try:
            LoginService.logout_all_sessions(request.user)
            
            return Response({
                'success': True,
                'message': '所有会话已登出'
            })
        
        except Exception as e:
            logger.error(f'登出所有会话失败: {request.user.username} - {str(e)}')
            return Response({
                'success': False,
                'message': '操作失败'
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(TokenRefreshView):
    """
    刷新Token视图
    """
    
    def post(self, request, *args, **kwargs):
        """刷新访问令牌"""
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                return Response({
                    'success': True,
                    'message': 'Token刷新成功',
                    'data': response.data
                })
            else:
                return response
        
        except (TokenError, InvalidToken) as e:
            return Response({
                'success': False,
                'message': 'Token刷新失败，请重新登录'
            }, status=status.HTTP_401_UNAUTHORIZED)


class PasswordChangeView(APIView):
    """
    修改密码视图
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """修改密码"""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'user': request.user}
        )
        
        if serializer.is_valid():
            try:
                old_password = serializer.validated_data['old_password']
                new_password = serializer.validated_data['new_password']
                
                # 修改密码
                PasswordService.change_password(request.user, old_password, new_password)
                
                return Response({
                    'success': True,
                    'message': '密码修改成功，请重新登录'
                })
            
            except Exception as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': '数据验证失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    """
    重置密码视图（管理员操作）
    """
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    
    @require_permission('user.change_password')
    def post(self, request):
        """重置用户密码"""
        serializer = PasswordResetSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                user_id = serializer.validated_data['user_id']
                new_password = serializer.validated_data['new_password']
                
                # 获取目标用户
                user = User.objects.get(id=user_id, tenant=request.user.tenant)
                
                # 检查权限
                if not request.user.can_manage_user(user):
                    return Response({
                        'success': False,
                        'message': '没有权限重置此用户密码'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # 重置密码
                PasswordService.reset_password(user, new_password)
                
                logger.info(f'管理员 {request.user.username} 重置了用户 {user.username} 的密码')
                
                return Response({
                    'success': True,
                    'message': '密码重置成功'
                })
            
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': '用户不存在'
                }, status=status.HTTP_404_NOT_FOUND)
            
            except Exception as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': False,
            'message': '数据验证失败',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """
    用户个人信息视图
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """获取当前用户信息"""
        user = request.user
        
        data = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'avatar': user.avatar.url if user.avatar else None,
            'tenant': {
                'id': str(user.tenant.id),
                'name': user.tenant.name
            } if user.tenant else None,
            'is_tenant_admin': user.is_tenant_admin,
            'roles': [role.name for role in user.roles.filter(is_active=True)],
            'permissions': list(user.get_all_permissions()),
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
            'language': user.language,
            'timezone_name': user.timezone_name,
        }
        
        # 获取用户配置
        if hasattr(user, 'profile'):
            profile = user.profile
            data['profile'] = {
                'real_name': profile.real_name,
                'birth_date': profile.birth_date.strftime('%Y-%m-%d') if profile.birth_date else None,
                'address': profile.address,
                'default_risk_level': profile.default_risk_level,
                'email_notifications': profile.email_notifications,
                'sms_notifications': profile.sms_notifications,
                'push_notifications': profile.push_notifications,
                'theme': profile.theme,
                'settings': profile.settings,
            }
        
        return Response({
            'success': True,
            'data': data
        })
    
    def put(self, request):
        """更新用户个人信息"""
        user = request.user
        
        # 更新基本信息
        allowed_fields = ['first_name', 'last_name', 'phone', 'email', 'language', 'timezone_name']
        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])
        
        try:
            user.save()
            
            # 更新或创建用户配置
            profile_data = request.data.get('profile', {})
            if profile_data:
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    tenant=user.tenant,
                    defaults=profile_data
                )
                
                if not created:
                    for field, value in profile_data.items():
                        if hasattr(profile, field):
                            setattr(profile, field, value)
                    profile.save()
            
            return Response({
                'success': True,
                'message': '个人信息更新成功'
            })
        
        except Exception as e:
            return Response({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class UserSessionView(APIView):
    """
    用户会话管理视图
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """获取用户活跃会话"""
        sessions = SessionService.get_active_sessions(request.user)
        
        data = []
        for session in sessions:
            data.append({
                'id': session.id,
                'ip_address': session.ip_address,
                'user_agent': session.user_agent,
                'device_info': session.device_info,
                'created_at': session.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'last_activity': session.last_activity.strftime('%Y-%m-%d %H:%M:%S'),
                'expires_at': session.expires_at.strftime('%Y-%m-%d %H:%M:%S'),
                'is_current': session.session_key in request.META.get('HTTP_AUTHORIZATION', '')
            })
        
        return Response({
            'success': True,
            'data': data
        })
    
    def delete(self, request, session_id):
        """终止指定会话"""
        try:
            success = SessionService.terminate_session(request.user, session_id)
            
            if success:
                return Response({
                    'success': True,
                    'message': '会话已终止'
                })
            else:
                return Response({
                    'success': False,
                    'message': '会话不存在或已过期'
                }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({
                'success': False,
                'message': '操作失败'
            }, status=status.HTTP_400_BAD_REQUEST)