/**
 * 顶部导航组件
 */

import React from 'react';
import { Layout, Button, Dropdown, Avatar, Space, Breadcrumb } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore, useAppStore } from '@/store';
import { useResponsive } from '@/hooks';
import { ROUTES } from '@/constants';

const { Header: AntHeader } = Layout;

const Header: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile } = useResponsive();
  const { user, logout } = useAuthStore();
  const { 
    sidebarCollapsed, 
    toggleSidebar, 
    mobileMenuOpen, 
    toggleMobileMenu,
    breadcrumbs 
  } = useAppStore();

  // 用户下拉菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate(ROUTES.PROFILE),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout,
    },
  ];

  // 处理侧边栏切换
  const handleToggleSidebar = () => {
    if (isMobile) {
      toggleMobileMenu();
    } else {
      toggleSidebar();
    }
  };

  return (
    <AntHeader className="app-header">
      <div className="header-left">
        {/* 菜单切换按钮 */}
        <Button
          type="text"
          icon={
            isMobile 
              ? (mobileMenuOpen ? <MenuFoldOutlined /> : <MenuUnfoldOutlined />)
              : (sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />)
          }
          onClick={handleToggleSidebar}
          className="sidebar-toggle"
        />

        {/* 面包屑导航 */}
        {breadcrumbs.length > 0 && (
          <Breadcrumb className="header-breadcrumb">
            {breadcrumbs.map((item, index) => (
              <Breadcrumb.Item key={index}>
                {item.path ? (
                  <a onClick={() => navigate(item.path!)}>{item.title}</a>
                ) : (
                  item.title
                )}
              </Breadcrumb.Item>
            ))}
          </Breadcrumb>
        )}
      </div>

      <div className="header-right">
        <Space size="middle">
          {/* 通知按钮 */}
          <Button
            type="text"
            icon={<BellOutlined />}
            className="notification-btn"
          />

          {/* 用户信息 */}
          <Dropdown
            menu={{ items: userMenuItems }}
            placement="bottomRight"
            trigger={['click']}
          >
            <div className="user-info">
              <Avatar
                size="small"
                icon={<UserOutlined />}
                src={user?.avatar}
              />
              {!isMobile && (
                <span className="username">{user?.username}</span>
              )}
            </div>
          </Dropdown>
        </Space>
      </div>
    </AntHeader>
  );
};

export default Header;