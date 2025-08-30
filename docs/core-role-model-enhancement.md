# 核心角色模型增强功能文档

## 变动概述

本次更新对 `backend/apps/core/models.py` 中的 `Role` 模型进行了重大增强，主要添加了角色优先级、颜色标识、循环继承检查、角色管理功能等特性，使角色系统更加完善和易用。

## 新增功能说明

### 1. 角色优先级系统

#### 新增字段
```python
priority = models.PositiveIntegerField('优先级', default=0)
```

**功能说明：**
- 数字越大优先级越高
- 用于角色排序和权限冲突解决
- 默认值为0，系统预定义角色有不同的优先级

**使用场景：**
- 角色列表按优先级排序显示
- 用户拥有多个角色时，按优先级确定最终权限
- 管理界面中重要角色优先显示

### 2. 角色颜色标识

#### 新增字段
```python
color = models.CharField('颜色标识', max_length=7, default='#1890FF')
```

**功能说明：**
- 存储16进制颜色值（如 #1890FF）
- 用于前端界面中角色的视觉区分
- 默认为蓝色（#1890FF）

**预定义颜色方案：**
- 超级管理员：`#F5222D`（红色）- 最高权限
- 管理员：`#FA8C16`（橙色）- 高权限  
- 交易员：`#52C41A`（绿色）- 中等权限
- 观察者：`#1890FF`（蓝色）- 基础权限

### 3. 循环继承检查

#### 新增方法
```python
def clean(self):
    """验证角色数据，防止循环继承"""
    
def _check_circular_inheritance(self, parent):
    """检查是否存在循环继承"""
```

**功能说明：**
- 防止角色A继承角色B，角色B又继承角色A的情况
- 使用递归算法检查整个继承链
- 在保存角色时自动验证

**算法逻辑：**
1. 从当前角色开始，递归检查父角色链
2. 如果在父角色链中发现当前角色，则存在循环
3. 抛出 `ValidationError` 阻止保存

### 4. 角色管理功能

#### 权限分析方法
```python
def get_inherited_permissions(self):
    """获取从父角色继承的权限"""
    
def get_direct_permissions(self):
    """获取角色直接拥有的权限"""
```

#### 角色关系管理
```python
def get_inheritance_chain(self):
    """获取角色继承链"""
    
def get_child_roles(self):
    """获取所有子角色"""
```

#### 角色删除检查
```python
def can_be_deleted(self):
    """检查角色是否可以被删除"""
```

**删除限制：**
1. 系统预定义角色不能删除
2. 正在被用户使用的角色不能删除
3. 有子角色的角色不能删除

#### 实用工具方法
```python
def get_user_count(self):
    """获取拥有此角色的用户数量"""
    
def copy_permissions_from(self, source_role):
    """从另一个角色复制权限"""
```

### 5. 系统角色自动创建

#### 类方法
```python
@classmethod
def create_system_roles(cls, tenant):
    """为租户创建系统预定义角色"""
```

**创建的角色：**

| 角色名称 | 优先级 | 颜色 | 权限范围 | 描述 |
|---------|--------|------|----------|------|
| 超级管理员 | 100 | #F5222D | 所有权限 | 拥有系统所有权限 |
| 管理员 | 80 | #FA8C16 | 用户、交易、策略、风险 | 大部分管理权限 |
| 交易员 | 60 | #52C41A | 交易、市场数据 | 交易相关权限 |
| 观察者 | 20 | #1890FF | 所有查看权限 | 只读权限 |

## 修改的功能说明

### 1. 模型排序规则

**修改前：**
```python
ordering = ['name']
```

**修改后：**
```python
ordering = ['-priority', 'name']
```

**影响：**
- 角色列表现在按优先级降序排列
- 相同优先级的角色按名称排序
- 重要角色会优先显示

### 2. 权限获取逻辑增强

原有的 `get_all_permissions()` 方法保持不变，但新增了更细粒度的权限分析方法，便于理解权限来源。

## 代码结构说明

### 类层次结构
```
Role (TenantModel)
├── 基础字段
│   ├── name (角色名称)
│   ├── description (角色描述)
│   ├── role_type (角色类型)
│   └── parent_role (父角色)
├── 新增字段
│   ├── priority (优先级)
│   └── color (颜色标识)
├── 关系字段
│   └── permissions (权限多对多关系)
└── 方法分类
    ├── 验证方法 (clean, _check_circular_inheritance)
    ├── 权限方法 (get_all_permissions, has_permission等)
    ├── 关系方法 (get_inheritance_chain, get_child_roles)
    ├── 管理方法 (can_be_deleted, get_user_count)
    └── 工具方法 (copy_permissions_from, create_system_roles)
```

### 数据库影响

**新增字段的迁移：**
```sql
ALTER TABLE core_role ADD COLUMN priority INTEGER DEFAULT 0 NOT NULL;
ALTER TABLE core_role ADD COLUMN color VARCHAR(7) DEFAULT '#1890FF' NOT NULL;
```

**索引优化：**
- 排序规则变更可能需要重新优化数据库索引
- 建议在 `(tenant_id, priority, name)` 上创建复合索引

## 使用示例

### 1. 创建带优先级的角色

```python
from apps.core.models import Role, Permission

# 创建高优先级角色
senior_trader = Role.objects.create(
    tenant=tenant,
    name='高级交易员',
    description='拥有高级交易权限的交易员',
    priority=70,
    color='#722ED1',  # 紫色
    role_type='custom'
)

# 添加权限
trading_permissions = Permission.objects.filter(
    category__in=['trading', 'market', 'risk']
)
senior_trader.permissions.set(trading_permissions)
```

### 2. 检查角色继承链

```python
# 获取角色的完整继承链
role = Role.objects.get(name='高级交易员')
inheritance_chain = role.get_inheritance_chain()

print("角色继承链：")
for i, role in enumerate(inheritance_chain):
    print(f"  {'  ' * i}└─ {role.name} (优先级: {role.priority})")
```

### 3. 权限分析

```python
role = Role.objects.get(name='交易员')

# 获取不同来源的权限
direct_perms = role.get_direct_permissions()
inherited_perms = role.get_inherited_permissions()
all_perms = role.get_all_permissions()

print(f"直接权限数量: {len(direct_perms)}")
print(f"继承权限数量: {len(inherited_perms)}")
print(f"总权限数量: {len(all_perms)}")
```

### 4. 角色删除检查

```python
role = Role.objects.get(name='观察者')
can_delete, reason = role.can_be_deleted()

if can_delete:
    role.delete()
    print("角色删除成功")
else:
    print(f"无法删除角色: {reason}")
```

### 5. 批量创建系统角色

```python
from apps.core.models import Role, Tenant

# 为新租户创建系统角色
tenant = Tenant.objects.create(name='新租户')
created_roles = Role.create_system_roles(tenant)

print(f"为租户 {tenant.name} 创建了 {len(created_roles)} 个系统角色")
for role in created_roles:
    print(f"  - {role.name} (优先级: {role.priority}, 颜色: {role.color})")
```

### 6. 权限复制

```python
# 从模板角色复制权限
template_role = Role.objects.get(name='交易员')
new_role = Role.objects.create(
    tenant=tenant,
    name='初级交易员',
    priority=50
)

# 复制权限
new_role.copy_permissions_from(template_role)
print(f"已从 {template_role.name} 复制权限到 {new_role.name}")
```

## 前端集成建议

### 1. 角色列表显示

```typescript
interface Role {
  id: string;
  name: string;
  description: string;
  priority: number;
  color: string;
  userCount: number;
  canDelete: boolean;
}

// 角色卡片组件
const RoleCard: React.FC<{ role: Role }> = ({ role }) => (
  <Card>
    <div style={{ borderLeft: `4px solid ${role.color}` }}>
      <h3>{role.name}</h3>
      <p>{role.description}</p>
      <Tag color={role.color}>优先级: {role.priority}</Tag>
      <span>{role.userCount} 个用户</span>
    </div>
  </Card>
);
```

### 2. 角色继承树

```typescript
// 角色继承树组件
const RoleInheritanceTree: React.FC<{ roles: Role[] }> = ({ roles }) => {
  const treeData = buildRoleTree(roles);
  
  return (
    <Tree
      treeData={treeData}
      titleRender={(node) => (
        <span style={{ color: node.color }}>
          {node.name} (优先级: {node.priority})
        </span>
      )}
    />
  );
};
```

### 3. 权限对比视图

```typescript
// 权限对比组件
const PermissionComparison: React.FC<{ roleId: string }> = ({ roleId }) => {
  const { directPerms, inheritedPerms } = useRolePermissions(roleId);
  
  return (
    <div>
      <h4>直接权限 ({directPerms.length})</h4>
      <PermissionList permissions={directPerms} type="direct" />
      
      <h4>继承权限 ({inheritedPerms.length})</h4>
      <PermissionList permissions={inheritedPerms} type="inherited" />
    </div>
  );
};
```

## 注意事项

### 1. 数据迁移

- **重要：** 升级前请备份数据库
- 新增字段有默认值，现有数据不会受影响
- 建议在低峰期执行迁移

### 2. 性能考虑

- 角色继承链检查使用递归，深度过大可能影响性能
- 建议限制角色继承层级不超过5层
- 大量角色时考虑添加缓存

### 3. 权限设计

- 优先级设计要考虑未来扩展
- 建议预留优先级区间（如：系统角色100-80，自定义角色79-1）
- 颜色选择要考虑可访问性和色盲用户

### 4. 安全注意事项

- 循环继承检查是安全关键功能，不要绕过
- 系统角色的删除限制不应被覆盖
- 权限复制操作要记录审计日志

### 5. 测试建议

```python
# 关键测试用例
class RoleModelTest(TestCase):
    def test_circular_inheritance_prevention(self):
        """测试循环继承防护"""
        
    def test_role_priority_ordering(self):
        """测试角色优先级排序"""
        
    def test_system_role_creation(self):
        """测试系统角色创建"""
        
    def test_role_deletion_constraints(self):
        """测试角色删除限制"""
        
    def test_permission_inheritance(self):
        """测试权限继承"""
```

## 后续优化建议

1. **缓存优化**：为角色权限查询添加缓存机制
2. **批量操作**：支持角色的批量权限分配
3. **权限模板**：预定义权限组合模板
4. **角色审计**：记录角色变更历史
5. **动态权限**：支持基于条件的动态权限分配

## 相关文档

- [多租户架构设计](multi-tenant-architecture.md)
- [权限管理系统](permission-management.md)
- [用户管理文档](user-management.md)
- [安全指南](security-guidelines.md)