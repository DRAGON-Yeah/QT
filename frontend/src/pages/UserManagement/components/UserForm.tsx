/**
 * 用户表单组件
 */
import React, { useState, useEffect } from 'react';
import { User, Role, UserProfile } from '../../../types';

interface UserFormProps {
  user?: User | null;
  roles: Role[];
  onSave: (userData: any) => Promise<void>;
  onCancel: () => void;
}

const UserForm: React.FC<UserFormProps> = ({ user, roles, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    passwordConfirm: '',
    firstName: '',
    lastName: '',
    phone: '',
    isTenantAdmin: false,
    roleIds: [] as number[],
    language: 'zh-hans',
    timezoneName: 'Asia/Shanghai',
    profileData: {
      defaultRiskLevel: 'medium' as 'low' | 'medium' | 'high',
      emailNotifications: true,
      smsNotifications: false,
      pushNotifications: true,
      theme: 'light' as 'light' | 'dark' | 'auto',
    } as Partial<UserProfile>,
  });

  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 初始化表单数据
  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username,
        email: user.email,
        password: '',
        passwordConfirm: '',
        firstName: user.firstName || '',
        lastName: user.lastName || '',
        phone: user.phone || '',
        isTenantAdmin: user.isTenantAdmin,
        roleIds: user.roles.map(role => role.id),
        language: user.language,
        timezoneName: user.timezoneName,
        profileData: {
          defaultRiskLevel: user.profile?.defaultRiskLevel || 'medium',
          emailNotifications: user.profile?.emailNotifications ?? true,
          smsNotifications: user.profile?.smsNotifications ?? false,
          pushNotifications: user.profile?.pushNotifications ?? true,
          theme: user.profile?.theme || 'light',
        },
      });
    }
  }, [user]);

  // 处理输入变化
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
    
    // 清除对应字段的错误
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  // 处理配置数据变化
  const handleProfileChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      profileData: {
        ...prev.profileData,
        [field]: value,
      },
    }));
  };

  // 处理角色选择
  const handleRoleChange = (roleId: number, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      roleIds: checked
        ? [...prev.roleIds, roleId]
        : prev.roleIds.filter(id => id !== roleId),
    }));
  };

  // 验证表单
  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.username.trim()) {
      newErrors.username = '用户名不能为空';
    }

    if (!formData.email.trim()) {
      newErrors.email = '邮箱不能为空';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = '邮箱格式不正确';
    }

    if (!user) { // 创建用户时需要密码
      if (!formData.password) {
        newErrors.password = '密码不能为空';
      } else if (formData.password.length < 8) {
        newErrors.password = '密码长度至少8位';
      }

      if (formData.password !== formData.passwordConfirm) {
        newErrors.passwordConfirm = '两次输入的密码不一致';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    try {
      await onSave(formData);
    } catch (error: any) {
      // 处理服务器返回的错误
      if (error.message && typeof error.message === 'object') {
        setErrors(error.message);
      } else {
        setErrors({ general: error.message || '保存失败' });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content user-form">
        <div className="modal-header">
          <h2>{user ? '编辑用户' : '创建用户'}</h2>
          <button className="modal-close" onClick={onCancel}>×</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {errors.general && (
            <div className="error-message">{errors.general}</div>
          )}

          {/* 基本信息 */}
          <div className="form-section">
            <h3>基本信息</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="username">用户名 *</label>
                <input
                  type="text"
                  id="username"
                  name="username"
                  value={formData.username}
                  onChange={handleInputChange}
                  disabled={!!user} // 编辑时不能修改用户名
                  className={errors.username ? 'error' : ''}
                />
                {errors.username && <span className="error-text">{errors.username}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="email">邮箱 *</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={errors.email ? 'error' : ''}
                />
                {errors.email && <span className="error-text">{errors.email}</span>}
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="firstName">名</label>
                <input
                  type="text"
                  id="firstName"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group">
                <label htmlFor="lastName">姓</label>
                <input
                  type="text"
                  id="lastName"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleInputChange}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="phone">手机号</label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
                />
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="isTenantAdmin"
                    checked={formData.isTenantAdmin}
                    onChange={handleInputChange}
                  />
                  租户管理员
                </label>
              </div>
            </div>
          </div>

          {/* 密码设置 */}
          {!user && (
            <div className="form-section">
              <h3>密码设置</h3>
              
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="password">密码 *</label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    className={errors.password ? 'error' : ''}
                  />
                  {errors.password && <span className="error-text">{errors.password}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="passwordConfirm">确认密码 *</label>
                  <input
                    type="password"
                    id="passwordConfirm"
                    name="passwordConfirm"
                    value={formData.passwordConfirm}
                    onChange={handleInputChange}
                    className={errors.passwordConfirm ? 'error' : ''}
                  />
                  {errors.passwordConfirm && <span className="error-text">{errors.passwordConfirm}</span>}
                </div>
              </div>
            </div>
          )}

          {/* 角色分配 */}
          <div className="form-section">
            <h3>角色分配</h3>
            <div className="role-list">
              {roles.map(role => (
                <label key={role.id} className="role-item">
                  <input
                    type="checkbox"
                    checked={formData.roleIds.includes(role.id)}
                    onChange={(e) => handleRoleChange(role.id, e.target.checked)}
                  />
                  <div className="role-info">
                    <div className="role-name">{role.name}</div>
                    <div className="role-description">{role.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* 系统设置 */}
          <div className="form-section">
            <h3>系统设置</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="language">语言</label>
                <select
                  id="language"
                  name="language"
                  value={formData.language}
                  onChange={handleInputChange}
                >
                  <option value="zh-hans">简体中文</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="timezoneName">时区</label>
                <select
                  id="timezoneName"
                  name="timezoneName"
                  value={formData.timezoneName}
                  onChange={handleInputChange}
                >
                  <option value="Asia/Shanghai">Asia/Shanghai</option>
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">America/New_York</option>
                </select>
              </div>
            </div>
          </div>

          {/* 个人偏好 */}
          <div className="form-section">
            <h3>个人偏好</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label>默认风险等级</label>
                <select
                  value={formData.profileData.defaultRiskLevel}
                  onChange={(e) => handleProfileChange('defaultRiskLevel', e.target.value)}
                >
                  <option value="low">低风险</option>
                  <option value="medium">中风险</option>
                  <option value="high">高风险</option>
                </select>
              </div>

              <div className="form-group">
                <label>主题</label>
                <select
                  value={formData.profileData.theme}
                  onChange={(e) => handleProfileChange('theme', e.target.value)}
                >
                  <option value="light">浅色</option>
                  <option value="dark">深色</option>
                  <option value="auto">自动</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.profileData.emailNotifications}
                    onChange={(e) => handleProfileChange('emailNotifications', e.target.checked)}
                  />
                  邮件通知
                </label>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.profileData.smsNotifications}
                    onChange={(e) => handleProfileChange('smsNotifications', e.target.checked)}
                  />
                  短信通知
                </label>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.profileData.pushNotifications}
                    onChange={(e) => handleProfileChange('pushNotifications', e.target.checked)}
                  />
                  推送通知
                </label>
              </div>
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

export default UserForm;