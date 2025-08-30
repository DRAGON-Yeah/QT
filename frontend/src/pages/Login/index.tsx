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

  /**
   * 处理登录表单提交
   * 
   * @param values - 表单数据，包含用户名和密码
   */
  const handleSubmit = async (values: LoginForm) => {
    try {
      // 设置加载状态
      setLoading(true);

      // 调用真实的登录API
      const { authService } = await import('@/services/authService');
      const response = await authService.login(values);

      // 更新全局认证状态
      login(response.user, response.access_token);
      
      // 显示成功提示
      message.success('登录成功');
      
      // 跳转到目标页面，使用replace避免返回到登录页
      navigate(from, { replace: true });

    } catch (error) {
      // 登录失败处理
      const errorMessage = error instanceof Error ? error.message : '登录失败，请检查用户名和密码';
      message.error(errorMessage);
    } finally {
      // 无论成功失败都要清除加载状态
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        {/* 登录页面头部 - 品牌标识和标题 */}
        <div className="login-header">
          <h1 className="login-title">QuantTrade</h1>
          <p className="login-subtitle">量化交易平台</p>
        </div>

        {/* 登录表单卡片容器 */}
        <Card className="login-card">
          <Form
            form={form}
            name="login"
            onFinish={handleSubmit}
            autoComplete="off"
            size="large"
          >
            {/* 用户名输入框 - 支持自动完成 */}
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

            {/* 密码输入框 - 自动隐藏输入内容 */}
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

            {/* 登录提交按钮 - 全宽度显示 */}
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

        {/* 页面底部版权信息 */}
        <div className="login-footer">
          <p>© 2025 QuantTrade. All rights reserved.</p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;