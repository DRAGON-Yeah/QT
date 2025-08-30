/**
 * 主布局组件
 */

import React from 'react';
import { Outlet } from 'react-router-dom';
import { Layout as AntLayout } from 'antd';
import Sidebar from './Sidebar';
import Header from './Header';
import { useResponsive } from '@/hooks';
import { useAppStore } from '@/store';
import './style.scss';

const { Content } = AntLayout;

const Layout: React.FC = () => {
  const { isMobile } = useResponsive();
  const { mobileMenuOpen, setMobileMenuOpen } = useAppStore();

  // 移动端点击遮罩关闭菜单
  const handleMaskClick = () => {
    if (isMobile && mobileMenuOpen) {
      setMobileMenuOpen(false);
    }
  };

  return (
    <AntLayout className="app-layout">
      {/* 侧边栏 */}
      <Sidebar />
      
      {/* 移动端遮罩 */}
      {isMobile && mobileMenuOpen && (
        <div className="mobile-mask" onClick={handleMaskClick} />
      )}
      
      {/* 主要内容区域 */}
      <AntLayout className="app-main">
        {/* 顶部导航 */}
        <Header />
        
        {/* 内容区域 */}
        <Content className="app-content">
          <div className="content-wrapper">
            <Outlet />
          </div>
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default Layout;