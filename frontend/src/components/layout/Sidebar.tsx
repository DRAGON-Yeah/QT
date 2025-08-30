/**
 * 侧边栏组件
 */

import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  BankOutlined,
  StockOutlined,
  CodeOutlined,
  LineChartOutlined,
  SafetyOutlined,
  SettingOutlined,
  UserOutlined,
  TeamOutlined,
  ProfileOutlined,
  MenuOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store';
import { useResponsive } from '@/hooks';
import { ROUTES } from '@/constants';
import classNames from 'classnames';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isMobile } = useResponsive();
  const { sidebarCollapsed, mobileMenuOpen, setMobileMenuOpen } = useAppStore();

  // 菜单项配置
  const menuItems = [
    {
      key: ROUTES.DASHBOARD,
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: ROUTES.USERS,
      icon: <TeamOutlined />,
      label: '用户管理',
    },
    {
      key: ROUTES.MENUS,
      icon: <MenuOutlined />,
      label: '菜单管理',
    },
    {
      key: ROUTES.EXCHANGES,
      icon: <BankOutlined />,
      label: '交易所管理',
    },
    {
      key: ROUTES.TRADING,
      icon: <StockOutlined />,
      label: '交易执行',
    },
    {
      key: ROUTES.STRATEGIES,
      icon: <CodeOutlined />,
      label: '策略管理',
    },
    {
      key: ROUTES.MARKET,
      icon: <LineChartOutlined />,
      label: '市场数据',
    },
    {
      key: ROUTES.RISK,
      icon: <SafetyOutlined />,
      label: '风险控制',
    },
    {
      key: ROUTES.SYSTEM,
      icon: <SettingOutlined />,
      label: '系统管理',
    },
    {
      key: ROUTES.PROFILE,
      icon: <ProfileOutlined />,
      label: '个人中心',
    },
  ];

  // 处理菜单点击
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    // 移动端点击菜单后关闭侧边栏
    if (isMobile) {
      setMobileMenuOpen(false);
    }
  };

  // 获取当前选中的菜单项
  const selectedKeys = [location.pathname];

  const siderClass = classNames('app-sidebar', {
    'app-sidebar--collapsed': sidebarCollapsed && !isMobile,
    'app-sidebar--mobile': isMobile,
    'app-sidebar--mobile-open': isMobile && mobileMenuOpen,
  });

  return (
    <Sider
      className={siderClass}
      collapsed={!isMobile && sidebarCollapsed}
      collapsedWidth={isMobile ? 0 : 64}
      width={240}
      breakpoint="lg"
      theme="dark"
    >
      {/* Logo 区域 */}
      <div className="sidebar-logo">
        <div className="logo-content">
          {(!sidebarCollapsed || isMobile) && (
            <span className="logo-text">QuantTrade</span>
          )}
          {sidebarCollapsed && !isMobile && (
            <span className="logo-icon">QT</span>
          )}
        </div>
      </div>

      {/* 菜单 */}
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={selectedKeys}
        items={menuItems}
        onClick={handleMenuClick}
        className="sidebar-menu"
      />
    </Sider>
  );
};

export default Sidebar;