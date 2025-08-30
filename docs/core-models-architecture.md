# QuantTrade 核心模型架构文档

## 变动概述

本次更新完成了 QuantTrade 系统的核心多租户架构模型设计，新增了完整的多租户基础模型、权限管理系统和菜单管理系统。这是系统多租户架构的核心基础，为后续所有业务模块提供了统一的数据隔离和权限控制机制。

## 新增功能说明

### 1. 多租户核心模型

#### 1.1 Tenant（租户模型）
- **功能**：多租户架构的核心，每个租户拥有独立的数据空间
- **特性**：
  - 使用 UUID 作为主键，确保全局唯一性
  - 支持租户级别的资源限制（用户数、策略数、交易所账户数）
  - 订阅管理功能，支持到期时间控制
  - 数据库模式名验证，确保符合命名规范

#### 1.2 TenantModel（多租户基础模型）
- **功能**：所有需要租户隔离的模型的抽象基类
- **特性**：
  - 自动租户关联和数据隔离
  - 双管理器设计（objects 和 all_objects）
  - 自动设置租户上下文
  - 创建和更新时间戳

#### 1.3 TenantManager（租户管理器）
- **功能**：自动过滤当前租户数据的查询管理器
- **特性**：
  - 透明的数据过滤机制
  - 与租户上下文无缝集成

### 2. 权限管理系统

#### 2.1 Permission（权限模型）
- **功能**：定义系统中的各种操作权限
- **特性**：
  - 权限分类管理（系统、用户、交易、策略等）
  - 支持内容类型关联
  - 权限代码唯一性约束

#### 2.2 Role（角色模型）
- **功能**：权限的集合，支持租户级别的角色定义
- **特性**：
  - 角色层级和权限继承
  - 系统预定义角色和自定义角色
  - 递归权限获取机制
  - 租户级别的角色隔离

### 3. 菜单管理系统

#### 3.1 Menu（菜单模型）
- **功能**：支持多级菜单结构和权限控制的菜单系统
- **特性**：
  - 树形菜单结构
  - 权限控制集成
  - 菜单类型支持（菜单、按钮、链接）
  - 排序和可见性控制

### 4. 工具函数库

#### 4.1 租户上下文管理
- **set_current_tenant()** / **get_current_tenant()**：线程级租户上下文
- **TenantContext**：租户上下文管理器
- **with_tenant()** / **ensure_tenant_context()**：装饰器支持

#### 4.2 缓存管理
- **get_tenant_cache_key()**：生成租户级缓存键
- **set_tenant_cache()** / **get_tenant_cache()**：租户级缓存操作
- **clear_tenant_cache()**：清理租户缓存

#### 4.3 权限和角色初始化
- **create_default_permissions()**：创建系统默认权限
- **create_default_roles()**：为租户创建默认角色

## 代码结构说明

### 模型继承关系
```
models.Model
├── Tenant（租户模型）
├── Permission（权限模型）
└── TenantModel（抽象基类）
    ├── Role（角色模型）
    └── Menu（菜单模型）
```

### 权限系统架构
```
用户 (User) ←→ 角色 (Role) ←→ 权限 (Permission)
     ↓              ↓              ↓
   租户隔离        租户隔离        全局共享
```

### 数据隔离机制
```
请求 → 中间件 → 设置租户上下文 → 模型查询 → 自动过滤租户数据
```

## 使用示例

### 1. 创建租户和用户
```python
from apps.core.models import Tenant
from apps.core.utils import create_default_roles, TenantContext

# 创建租户
tenant = Tenant.objects.create(
    name='示例公司',
    schema_name='example_company',
    max_users=50,
    max_strategies=20
)

# 为租户创建默认角色
with TenantContext(tenant):
    roles = create_default_roles(tenant)
    print(f"创建了 {len(roles)} 个默认角色")
```

### 2. 权限检查
```python
from apps.core.utils import ensure_tenant_context

@ensure_tenant_context
def create_trading_order(user, order_data):
    """创建交易订单（需要租户上下文）"""
    # 检查用户权限
    if not user.has_permission('trading.create_order'):
        raise PermissionDenied('无创建订单权限')
    
    # 创建订单逻辑
    pass
```

### 3. 菜单权限控制
```python
def get_user_menu(user):
    """获取用户可访问的菜单"""
    menus = Menu.objects.filter(
        is_active=True,
        is_visible=True,
        parent__isnull=True
    ).order_by('sort_order')
    
    accessible_menus = []
    for menu in menus:
        if menu.has_permission(user):
            accessible_menus.append(menu)
    
    return accessible_menus
```

### 4. 租户级缓存使用
```python
from apps.core.utils import set_tenant_cache, get_tenant_cache

def get_user_dashboard_data(user):
    """获取用户仪表盘数据（带缓存）"""
    cache_key = f'dashboard_data_{user.id}'
    
    # 尝试从租户缓存获取
    data = get_tenant_cache(cache_key)
    if data is None:
        # 生成数据
        data = generate_dashboard_data(user)
        # 缓存1小时
        set_tenant_cache(cache_key, data, timeout=3600)
    
    return data
```

## 数据库设计

### 核心表结构
```sql
-- 租户表
CREATE TABLE core_tenant (
    id UUID PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    schema_name VARCHAR(63) UNIQUE NOT NULL,
    domain VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    max_users INTEGER DEFAULT 100,
    max_strategies INTEGER DEFAULT 50,
    max_exchange_accounts INTEGER DEFAULT 10,
    subscription_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 权限表
CREATE TABLE core_permission (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    codename VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(20) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 角色表
CREATE TABLE core_role (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    role_type VARCHAR(10) DEFAULT 'custom',
    parent_role_id INTEGER REFERENCES core_role(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

-- 菜单表
CREATE TABLE core_menu (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    title VARCHAR(100) NOT NULL,
    icon VARCHAR(50),
    path VARCHAR(200),
    component VARCHAR(200),
    parent_id INTEGER REFERENCES core_menu(id),
    sort_order INTEGER DEFAULT 0,
    is_visible BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    menu_type VARCHAR(10) DEFAULT 'menu',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);
```

### 索引优化
```sql
-- 租户相关索引
CREATE INDEX idx_tenant_active ON core_tenant(is_active);
CREATE INDEX idx_tenant_domain ON core_tenant(domain) WHERE domain IS NOT NULL;

-- 角色权限索引
CREATE INDEX idx_role_tenant ON core_role(tenant_id);
CREATE INDEX idx_role_active ON core_role(tenant_id, is_active);
CREATE INDEX idx_role_parent ON core_role(parent_role_id);

-- 菜单索引
CREATE INDEX idx_menu_tenant ON core_menu(tenant_id);
CREATE INDEX idx_menu_parent ON core_menu(parent_id);
CREATE INDEX idx_menu_visible ON core_menu(tenant_id, is_visible, is_active);
CREATE INDEX idx_menu_sort ON core_menu(tenant_id, parent_id, sort_order);
```

## 安全考虑

### 1. 数据隔离
- **强制租户过滤**：所有查询自动添加租户过滤条件
- **上下文验证**：关键操作必须在租户上下文中执行
- **管理器分离**：普通查询和管理员查询使用不同管理器

### 2. 权限控制
- **最小权限原则**：默认角色遵循最小权限原则
- **权限继承**：支持角色层级和权限继承
- **动态权限检查**：运行时权限验证

### 3. 输入验证
- **模式名验证**：确保数据库模式名符合规范
- **唯一性约束**：关键字段的唯一性约束
- **数据完整性**：外键约束保证数据一致性

## 性能优化

### 1. 查询优化
- **索引策略**：为常用查询字段建立复合索引
- **查询缓存**：租户级别的查询结果缓存
- **预加载优化**：使用 select_related 和 prefetch_related

### 2. 缓存策略
- **多级缓存**：租户级 + 用户级缓存
- **缓存失效**：智能缓存失效机制
- **缓存预热**：系统启动时预热常用数据

### 3. 数据库优化
- **连接池**：数据库连接池配置
- **分区表**：大数据量表的分区策略
- **读写分离**：读写分离架构支持

## 注意事项

### 1. 开发注意事项
- **继承 TenantModel**：所有业务模型必须继承 TenantModel
- **租户上下文**：确保在正确的租户上下文中操作
- **权限检查**：关键操作前进行权限验证
- **缓存键命名**：使用统一的租户缓存键命名规范

### 2. 部署注意事项
- **数据迁移**：租户数据的迁移策略
- **备份策略**：租户级别的数据备份
- **监控告警**：租户级别的监控和告警

### 3. 扩展性考虑
- **水平扩展**：支持多数据库的租户分布
- **垂直扩展**：单租户的资源扩展
- **跨租户操作**：特殊场景下的跨租户数据访问

## 后续开发指南

### 1. 创建新的业务模型
```python
from apps.core.models import TenantModel

class YourBusinessModel(TenantModel):
    """你的业务模型"""
    name = models.CharField('名称', max_length=100)
    # 其他字段...
    
    class Meta:
        db_table = 'your_business_model'
        verbose_name = '业务模型'
        verbose_name_plural = '业务模型'
```

### 2. 添加新权限
```python
# 在 create_default_permissions() 中添加
('your_module.your_action', '你的操作', 'your_category'),
```

### 3. 创建视图权限控制
```python
from apps.core.utils import ensure_tenant_context
from apps.core.permissions import require_permission

class YourAPIView(APIView):
    @ensure_tenant_context
    @require_permission('your_module.your_action')
    def post(self, request):
        # 你的业务逻辑
        pass
```

这个核心模型架构为 QuantTrade 系统提供了坚实的多租户基础，确保了数据安全、权限控制和系统扩展性。