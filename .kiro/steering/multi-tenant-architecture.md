# 多租户架构设计指南

## 多租户核心原则
- **数据隔离**：每个租户拥有独立的数据空间，确保数据完全隔离
- **权限控制**：基于RBAC模型的细粒度权限控制
- **资源隔离**：计算资源和存储资源独立分配
- **环境隔离**：Python虚拟环境(.venv)确保依赖包版本一致性

## 数据隔离策略
### 数据库层面隔离
```python
# 每个模型都需要包含租户字段
class BaseModel(models.Model):
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# 自定义Manager确保查询时自动过滤租户
class TenantManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(tenant=get_current_tenant())
```

### 中间件实现租户上下文
```python
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 从JWT token中提取租户信息
        tenant = self.get_tenant_from_request(request)
        set_current_tenant(tenant)
        
        response = self.get_response(request)
        return response
```

## 权限管理架构
### RBAC权限模型
- **用户(User)**：系统用户，仅由管理员创建
- **角色(Role)**：权限的集合，如管理员、交易员、观察者
- **权限(Permission)**：具体的功能权限
- **租户(Tenant)**：数据隔离的基本单位

### 权限检查装饰器
```python
def require_permission(permission_name):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.has_permission(permission_name):
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

## 用户管理策略
### 仅管理员创建用户
- 系统不提供用户注册功能
- 所有用户账户由系统管理员在后台创建
- 用户创建时自动分配租户和初始角色
- 支持批量用户导入和管理

### 用户认证流程
```python
# JWT认证包含租户信息
def generate_jwt_token(user):
    payload = {
        'user_id': user.id,
        'tenant_id': user.tenant.id,
        'roles': [role.name for role in user.roles.all()],
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
```

## 数据访问控制
### QuerySet自动过滤
```python
# 所有查询自动添加租户过滤
class TenantQuerySet(models.QuerySet):
    def filter_by_tenant(self):
        return self.filter(tenant=get_current_tenant())

class TenantModel(BaseModel):
    objects = TenantManager.from_queryset(TenantQuerySet)()
    
    class Meta:
        abstract = True
```

### API视图基类
```python
class TenantAPIView(APIView):
    def get_queryset(self):
        return super().get_queryset().filter(tenant=self.request.user.tenant)
    
    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)
```

## 资源隔离
### 文件存储隔离
```python
def tenant_upload_path(instance, filename):
    return f'tenant_{instance.tenant.id}/{filename}'

class Document(TenantModel):
    file = models.FileField(upload_to=tenant_upload_path)
```

### 缓存隔离
```python
def get_tenant_cache_key(key):
    tenant_id = get_current_tenant().id
    return f'tenant_{tenant_id}:{key}'

def set_tenant_cache(key, value, timeout=3600):
    cache_key = get_tenant_cache_key(key)
    cache.set(cache_key, value, timeout)
```

## 多租户测试策略
### 测试数据隔离
```python
class TenantTestCase(TestCase):
    def setUp(self):
        self.tenant1 = Tenant.objects.create(name='Tenant 1')
        self.tenant2 = Tenant.objects.create(name='Tenant 2')
        self.user1 = User.objects.create(username='user1', tenant=self.tenant1)
        self.user2 = User.objects.create(username='user2', tenant=self.tenant2)
    
    def test_data_isolation(self):
        # 确保租户1的用户无法访问租户2的数据
        pass
```

## 性能优化
### 数据库索引策略
```sql
-- 所有多租户表都需要在tenant_id上建立索引
CREATE INDEX idx_table_tenant_id ON table_name(tenant_id);

-- 复合索引包含tenant_id
CREATE INDEX idx_table_tenant_created ON table_name(tenant_id, created_at);
```

### 查询优化
- 所有查询都必须包含租户过滤条件
- 使用select_related和prefetch_related优化关联查询
- 避免跨租户的复杂查询

## 监控和审计
### 租户级别监控
- 每个租户的资源使用情况监控
- 租户级别的性能指标统计
- 数据访问审计日志

### 安全审计
- 记录所有跨租户访问尝试
- 权限变更审计日志
- 异常访问模式检测