# JWT认证系统实现文档

## 概述

本文档描述了QuantTrade系统中JWT认证和权限控制系统的实现。该系统基于Django REST Framework和django-rest-framework-simplejwt，提供了完整的多租户认证和权限管理功能。

## 核心组件

### 1. JWT认证服务 (`apps/users/authentication.py`)

#### JWTService
- **功能**: JWT token的生成、验证和刷新
- **主要方法**:
  - `generate_tokens()`: 生成访问令牌和刷新令牌
  - `verify_token()`: 验证JWT token
  - `refresh_token()`: 刷新访问令牌
  - `revoke_token()`: 撤销token

#### CustomJWTAuthentication
- **功能**: 扩展django-rest-framework-simplejwt的认证功能
- **特性**:
  - 用户状态检查（激活、锁定）
  - 租户状态验证
  - 会话管理
  - 活动时间更新

#### LoginService
- **功能**: 处理用户登录逻辑
- **特性**:
  - 用户认证
  - 登录日志记录
  - 失败次数跟踪
  - 账户锁定机制

#### PasswordService
- **功能**: 密码管理服务
- **特性**:
  - 密码强度验证
  - 密码修改
  - 密码重置
  - 安全策略执行

#### SessionService
- **功能**: 用户会话管理
- **特性**:
  - 活跃会话查询
  - 会话终止
  - 过期会话清理

### 2. 权限控制系统 (`apps/core/permissions.py`)

#### 权限装饰器
- `@require_permission()`: 单权限检查
- `@require_permissions()`: 多权限检查（AND逻辑）
- `@require_any_permission()`: 任一权限检查（OR逻辑）
- `@require_role()`: 角色检查
- `@require_tenant_admin`: 租户管理员检查
- `@require_superuser`: 超级用户检查

#### 权限类
- `TenantPermission`: 租户权限控制
- `AdminPermission`: 管理员权限控制
- `SuperAdminPermission`: 超级管理员权限控制
- `CustomPermission`: 自定义权限控制

#### 权限混入类
- `PermissionMixin`: 用于类视图的权限控制
- `APIPermissionMixin`: 用于DRF视图的权限控制

### 3. 多租户中间件 (`apps/core/middleware.py`)

#### TenantMiddleware
- **功能**: 租户上下文识别和设置
- **识别优先级**:
  1. HTTP头部 X-Tenant-ID
  2. 用户所属租户（已认证用户）
  3. 域名映射
  4. 默认租户

#### TenantAccessControlMiddleware
- **功能**: 租户访问控制
- **特性**:
  - 用户租户匹配验证
  - 跨租户访问阻止
  - 超级用户例外处理

#### TenantSecurityMiddleware
- **功能**: 安全审计和日志
- **特性**:
  - 敏感操作记录
  - 访问日志记录
  - 安全事件监控

### 4. 用户模型扩展 (`apps/users/models.py`)

#### User模型
- **扩展字段**:
  - 租户关联
  - 角色关联
  - 安全设置（锁定、失败次数）
  - 活动跟踪

- **主要方法**:
  - `get_all_permissions()`: 获取所有权限
  - `has_permission()`: 权限检查
  - `has_role()`: 角色检查
  - `add_role()` / `remove_role()`: 角色管理
  - `is_account_locked()`: 账户锁定检查
  - `record_failed_login()`: 记录登录失败

#### 相关模型
- `UserRole`: 用户角色关联
- `UserProfile`: 用户配置信息
- `UserSession`: 用户会话记录
- `LoginLog`: 登录日志

### 5. API视图 (`apps/users/views.py`)

#### 认证相关视图
- `LoginView`: 用户登录
- `LogoutView`: 用户登出
- `LogoutAllView`: 登出所有会话
- `RefreshTokenView`: 刷新token
- `PasswordChangeView`: 修改密码
- `PasswordResetView`: 重置密码
- `UserProfileView`: 用户信息
- `UserSessionView`: 会话管理

#### 用户管理视图
- `UserManagementViewSet`: 用户CRUD操作
- `RoleManagementViewSet`: 角色管理
- `PermissionListView`: 权限列表
- `RoleAssignmentView`: 角色分配

## 配置说明

### Django设置 (`config/settings/base.py`)

```python
# JWT配置
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# REST Framework配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.authentication.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# 中间件配置
MIDDLEWARE = [
    # ... 其他中间件
    'apps.core.middleware.TenantMiddleware',
    # ... 其他中间件
]
```

### URL配置 (`apps/users/urls.py`)

```python
urlpatterns = [
    # JWT认证相关
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    
    # 密码管理
    path('auth/change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('auth/reset-password/', PasswordResetView.as_view(), name='reset-password'),
    
    # 用户信息和会话
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('sessions/', UserSessionView.as_view(), name='user-sessions'),
    
    # 用户和角色管理
    path('', include(router.urls)),
]
```

## API使用示例

### 1. 用户登录

```bash
POST /api/users/auth/login/
Content-Type: application/json

{
    "username": "testuser",
    "password": "testpass123"
}
```

响应：
```json
{
    "success": true,
    "message": "登录成功",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            "id": "uuid",
            "username": "testuser",
            "email": "test@example.com",
            "tenant_id": "tenant-uuid",
            "roles": ["观察者"],
            "permissions": ["trading.view_orders"]
        }
    }
}
```

### 2. 访问受保护的API

```bash
GET /api/users/profile/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Tenant-ID: tenant-uuid
```

### 3. 刷新Token

```bash
POST /api/users/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. 修改密码

```bash
POST /api/users/auth/change-password/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
    "old_password": "oldpass123",
    "new_password": "newpass123",
    "new_password_confirm": "newpass123"
}
```

### 5. 用户登出

```bash
POST /api/users/auth/logout/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## 安全特性

### 1. 密码安全
- 最小长度8位
- 必须包含大小写字母、数字和特殊字符
- 密码哈希存储
- 密码修改时间跟踪

### 2. 账户安全
- 登录失败次数限制（5次）
- 账户自动锁定机制
- 登录日志记录
- 异常登录检测

### 3. Token安全
- JWT签名验证
- Token过期机制
- Token黑名单支持
- 会话管理和跟踪

### 4. 多租户安全
- 租户数据隔离
- 跨租户访问阻止
- 租户状态验证
- 权限租户级别控制

### 5. 审计和监控
- 登录日志记录
- 敏感操作审计
- 安全事件监控
- 访问日志记录

## 测试

### 单元测试
- JWT服务测试
- 权限系统测试
- 密码服务测试
- 会话管理测试

### 集成测试
- API端点测试
- 认证流程测试
- 权限控制测试
- 多租户隔离测试

### 测试运行
```bash
# 运行JWT认证系统测试
python test_jwt_auth.py

# 运行API端点测试
python test_api_endpoints.py

# 运行Django单元测试
python manage.py test apps.users.tests.JWTAuthenticationTest
```

## 部署注意事项

### 1. 环境变量
```bash
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here
```

### 2. 数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. 创建默认权限和角色
```python
from apps.core.utils import create_default_permissions, create_default_roles
from apps.core.models import Tenant

# 创建权限
create_default_permissions()

# 为每个租户创建角色
for tenant in Tenant.objects.all():
    create_default_roles(tenant)
```

### 4. 性能优化
- 使用Redis缓存JWT验证结果
- 定期清理过期会话和日志
- 数据库索引优化
- 连接池配置

## 故障排除

### 常见问题

1. **Token验证失败**
   - 检查SECRET_KEY配置
   - 验证Token格式
   - 检查Token是否过期

2. **权限检查失败**
   - 验证用户角色分配
   - 检查权限配置
   - 确认租户上下文

3. **租户上下文缺失**
   - 检查中间件配置
   - 验证HTTP头部设置
   - 确认用户租户关联

4. **会话管理问题**
   - 检查数据库连接
   - 验证会话清理任务
   - 确认Redis配置

### 日志分析
```bash
# 查看认证相关日志
tail -f logs/django.log | grep "authentication"

# 查看安全相关日志
tail -f logs/security.log

# 查看权限相关日志
tail -f logs/django.log | grep "permission"
```

## 总结

JWT认证系统为QuantTrade提供了完整的多租户认证和权限控制功能，具有以下特点：

1. **安全性**: 多层安全防护，包括密码策略、账户锁定、Token管理等
2. **可扩展性**: 支持自定义权限、角色和认证策略
3. **多租户**: 完整的租户隔离和上下文管理
4. **易用性**: 简洁的API接口和装饰器使用
5. **可监控**: 完整的日志记录和审计功能

该系统已通过完整的测试验证，可以安全地用于生产环境。