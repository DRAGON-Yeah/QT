/**
 * 角色管理组件
 */
import React, { useState, useEffect } from 'react';
import { Role, Permission } from '../../../types';
import { userService } from '../../../services/userService';

interface RoleManagementProps {
  roles: Role[];
  onRoleChange: () => void;
}

const RoleManagement: React.FC<RoleManagementProps> = ({ roles, onRoleChange }) => {
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [permissions, setPermissions] = useState<Record<string, Permission[]>>({});
  const [showRoleForm, setShowRoleForm] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [loading, setLoading] = useState(false);

  // 加载权限列表
  useEffect(() => {
    loadPermissions();
  }, []);

  const loadPermissions = async () => {
    try {
      const permissionsData = await userService.getPermissionList();
      setPermissions(permissionsData);
    } catch (error) {
      console.error('加载权限列表失败:', error);
    }
  };

  // 创建角色
  const handleCreateRole = () => {
    setEditingRole(null);
    setShowRoleForm(true);
  };

  // 编辑角色
  const handleEditRole = (role: Role) => {
    setEditingRole(role);
    setShowRoleForm(true);
  };

  // 删除角色
  const handleDeleteRole = async (roleId: number) => {
    if (!confirm('确定要删除此角色吗？')) {
      return;
    }

    try {
      await userService.deleteRole(roleId);
      onRoleChange();
      if (selectedRole?.id === roleId) {
        setSelectedRole(null);
      }
    } catch (error) {
      console.error('删除角色失败:', error);
      alert('删除失败：' + (error as Error).message);
    }
  };

  return (
    <div className="role-management">
      <div className="role-management__layout">
        {/* 左侧角色列表 */}
        <div className="role-management__sidebar">
          <div className="role-management__header">
            <h3>角色列表</h3>
            <button className="btn btn-primary btn-small" onClick={handleCreateRole}>
              创建角色
            </button>
          </div>

          <div className="role-list">
            {roles.map(role => (
              <div
                key={role.id}
                className={`role-item ${selectedRole?.id === role.id ? 'active' : ''}`}
                onClick={() => setSelectedRole(role)}
              >
                <div className="role-item__header">
                  <div className="role-item__name">{role.name}</div>
                  <div className="role-item__type">
                    {role.roleType === 'system' ? '系统' : '自定义'}
                  </div>
                </div>
                <div className="role-item__description">{role.description}</div>
                <div className="role-item__stats">
                  <span>权限: {role.permissions.length}</span>
                  <span>用户: {role.userCount || 0}</span>
                </div>
                <div className="role-item__actions">
                  <button onClick={(e) => {
                    e.stopPropagation();
                    handleEditRole(role);
                  }}>
                    编辑
                  </button>
                  {role.roleType !== 'system' && (
                    <button 
                      className="danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteRole(role.id);
                      }}
                    >
                      删除
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 右侧权限配置 */}
        <div className="role-management__content">
          {selectedRole ? (
            <RolePermissions
              role={selectedRole}
              permissions={permissions}
              onUpdate={onRoleChange}
            />
          ) : (
            <div className="role-management__placeholder">
              <div className="placeholder-content">
                <h3>选择角色</h3>
                <p>请从左侧选择一个角色来查看和编辑权限</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 角色表单弹窗 */}
      {showRoleForm && (
        <RoleForm
          role={editingRole}
          permissions={permissions}
          onSave={async (roleData) => {
            try {
              if (editingRole) {
                await userService.updateRole(editingRole.id, roleData);
              } else {
                await userService.createRole(roleData);
              }
              setShowRoleForm(false);
              setEditingRole(null);
              onRoleChange();
            } catch (error) {
              console.error('保存角色失败:', error);
              throw error;
            }
          }}
          onCancel={() => {
            setShowRoleForm(false);
            setEditingRole(null);
          }}
        />
      )}
    </div>
  );
};

// 角色权限组件
interface RolePermissionsProps {
  role: Role;
  permissions: Record<string, Permission[]>;
  onUpdate: () => void;
}

const RolePermissions: React.FC<RolePermissionsProps> = ({ role, permissions, onUpdate }) => {
  const [selectedPermissions, setSelectedPermissions] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setSelectedPermissions(role.permissions.map(p => p.id));
  }, [role]);

  // 处理权限选择
  const handlePermissionChange = (permissionId: number, checked: boolean) => {
    setSelectedPermissions(prev => 
      checked 
        ? [...prev, permissionId]
        : prev.filter(id => id !== permissionId)
    );
  };

  // 处理分类全选
  const handleCategoryToggle = (categoryPermissions: Permission[], checked: boolean) => {
    const categoryIds = categoryPermissions.map(p => p.id);
    setSelectedPermissions(prev => 
      checked
        ? [...new Set([...prev, ...categoryIds])]
        : prev.filter(id => !categoryIds.includes(id))
    );
  };

  // 保存权限
  const handleSavePermissions = async () => {
    setLoading(true);
    try {
      await userService.updateRole(role.id, {
        permissionIds: selectedPermissions
      });
      onUpdate();
    } catch (error) {
      console.error('保存权限失败:', error);
      alert('保存失败：' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="role-permissions">
      <div className="role-permissions__header">
        <div>
          <h3>{role.name} - 权限配置</h3>
          <p>{role.description}</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={handleSavePermissions}
          disabled={loading}
        >
          {loading ? '保存中...' : '保存权限'}
        </button>
      </div>

      <div className="permissions-grid">
        {Object.entries(permissions).map(([category, categoryPermissions]) => {
          const selectedCount = categoryPermissions.filter(p => 
            selectedPermissions.includes(p.id)
          ).length;
          const isAllSelected = selectedCount === categoryPermissions.length;
          const isPartialSelected = selectedCount > 0 && selectedCount < categoryPermissions.length;

          return (
            <div key={category} className="permission-category">
              <div className="permission-category__header">
                <label className="permission-category__title">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    ref={input => {
                      if (input) input.indeterminate = isPartialSelected;
                    }}
                    onChange={(e) => handleCategoryToggle(categoryPermissions, e.target.checked)}
                  />
                  <span>{category}</span>
                  <span className="permission-count">({selectedCount}/{categoryPermissions.length})</span>
                </label>
              </div>

              <div className="permission-list">
                {categoryPermissions.map(permission => (
                  <label key={permission.id} className="permission-item">
                    <input
                      type="checkbox"
                      checked={selectedPermissions.includes(permission.id)}
                      onChange={(e) => handlePermissionChange(permission.id, e.target.checked)}
                    />
                    <div className="permission-info">
                      <div className="permission-name">{permission.name}</div>
                      <div className="permission-description">{permission.description}</div>
                      <div className="permission-codename">{permission.codename}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// 角色表单组件
interface RoleFormProps {
  role?: Role | null;
  permissions: Record<string, Permission[]>;
  onSave: (roleData: any) => Promise<void>;
  onCancel: () => void;
}

const RoleForm: React.FC<RoleFormProps> = ({ role, permissions, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permissionIds: [] as number[],
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (role) {
      setFormData({
        name: role.name,
        description: role.description,
        permissionIds: role.permissions.map(p => p.id),
      });
    }
  }, [role]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name.trim()) {
      setErrors({ name: '角色名称不能为空' });
      return;
    }

    setLoading(true);
    try {
      await onSave(formData);
    } catch (error: any) {
      setErrors({ general: error.message || '保存失败' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content role-form">
        <div className="modal-header">
          <h2>{role ? '编辑角色' : '创建角色'}</h2>
          <button className="modal-close" onClick={onCancel}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {errors.general && (
            <div className="error-message">{errors.general}</div>
          )}

          <div className="form-group">
            <label htmlFor="name">角色名称 *</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
              className={errors.name ? 'error' : ''}
            />
            {errors.name && <span className="error-text">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="description">角色描述</label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              rows={3}
            />
          </div>

          <div className="form-group">
            <label>权限配置</label>
            <div className="permissions-grid">
              {Object.entries(permissions).map(([category, categoryPermissions]) => (
                <div key={category} className="permission-category">
                  <div className="permission-category__title">{category}</div>
                  <div className="permission-list">
                    {categoryPermissions.map(permission => (
                      <label key={permission.id} className="permission-item">
                        <input
                          type="checkbox"
                          checked={formData.permissionIds.includes(permission.id)}
                          onChange={(e) => {
                            const checked = e.target.checked;
                            setFormData(prev => ({
                              ...prev,
                              permissionIds: checked
                                ? [...prev.permissionIds, permission.id]
                                : prev.permissionIds.filter(id => id !== permission.id)
                            }));
                          }}
                        />
                        <span>{permission.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </form>

        <div className="modal-footer">
          <button type="button" onClick={onCancel} disabled={loading}>
            取消
          </button>
          <button 
            type="submit" 
            onClick={handleSubmit}
            className="btn-primary" 
            disabled={loading}
          >
            {loading ? '保存中...' : '保存'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RoleManagement;