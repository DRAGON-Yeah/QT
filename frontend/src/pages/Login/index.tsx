/**
 * QuantTrade 登录页面组件
 * 
 * 功能说明：
 * - 提供用户登录界面
 * - 支持用户名和密码验证
 * - 登录成功后跳转到指定页面
 * - 集成多租户认证机制
 * - 响应式设计，支持多设备访问
 */

import React from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { ROUTES } from '@/constants';
import './style.scss';

/**
 * 登录表单数据接口
 */
interface LoginForm {
  username: string; // 用户名
  password: string; // 密码
}

/**
 * 登录页面主组件
 * 
 * @returns React 函数组件
 */
const LoginPage: React.FC = () => {
  // React Router 导航钩子
  const navigate = useNavigate();
  const location = useLocation();
  
  // 认证状态管理
  const { login, setLoading, loading } = useAuthStore();
  
  // Ant Design 表单实例
  const [form] = Form.useForm();

  // 获取登录成功后的重定向路径，默认跳转到仪表盘
  const from = (location.state as any)?.from || ROUTES.DASHBOARD;

  const handleSubmit = async (values: LoginForm) => {
    try {
      setLoading(true);

      // TODO: 调用登录API
      // const response = await authService.login(values);

      // 模拟登录成功
      const mockUser = {
        id: 1,
        username: values.username,
        email: `${values.username}@example.com`,
        tenant: {
          id: 1,
          name: '测试租户',
          schemaName: 'tenant_1',
          isActive: true,
          createdAt: new Date().toISOString(),
        },
        roles: [
          {
            id: 1,
            name: '管理员',
            permissions: [
              { id: 1, name: '用户管理', codename: 'users.manage' },
              { id: 2, name: '交易管理', codename: 'trading.manage' },
            ],
          },
        ],
        permissions: ['users.manage', 'trading.manage'],
        isActive: true,
      };

      const mockToken = 'mock-jwt-token';

      login(mockUser, mockToken);
      message.success('登录成功');
      navigate(from, { replace: true });

    } catch (error) {
      message.error('登录失败，请检查用户名和密码');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h1 className="login-title">QuantTrade</h1>
          <p className="login-subtitle">量化交易平台</p>
        </div>

        <Card className="login-card">
          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            autoComplete="off"
            size="large"
          >
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                autoComplete="username"
              />
            </Form.Item>

            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                autoComplete="current-password"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
              >
                登录
              </Button>
            </Form.Item>
          </Form>
        </Card>

        <div className="login-footer">
          <p>© 2025~2035 QuantTrade. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;