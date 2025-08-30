/**
 * 侧边栏悬浮菜单测试组件
 * 
 * 用于测试侧边栏在收起状态下的悬浮菜单功能
 * 提供交互式界面来验证菜单的展开/收起行为和悬浮效果
 */

import React from 'react';
import { Button, Space } from 'antd';
import Sidebar from './Sidebar';
import { useAppStore } from '@/store';

/**
 * 侧边栏测试组件
 * 
 * 功能特性:
 * - 提供侧边栏状态切换按钮
 * - 显示当前侧边栏状态
 * - 包含详细的测试说明和操作指南
 * - 模拟真实的布局环境进行测试
 */
const SidebarTest: React.FC = () => {
  // 从全局状态管理中获取侧边栏状态和控制函数
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore();

  /**
   * 切换侧边栏展开/收起状态
   */
  const handleToggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      {/* 侧边栏组件 */}
      <Sidebar />
      
      {/* 主内容区域 */}
      <div style={{ flex: 1, padding: '20px' }}>
        <Space direction="vertical" size="large">
          <h2>侧边栏悬浮菜单测试</h2>
          
          {/* 状态显示 */}
          <p>当前状态: {sidebarCollapsed ? '已收起' : '已展开'}</p>
          
          {/* 状态切换按钮 */}
          <Button 
            type="primary" 
            onClick={handleToggleSidebar}
          >
            {sidebarCollapsed ? '展开侧边栏' : '收起侧边栏'}
          </Button>
          
          {/* 测试说明 */}
          <div>
            <h3>测试说明:</h3>
            <ul>
              <li>点击上方按钮收起侧边栏</li>
              <li>将鼠标悬停在有子菜单的一级菜单图标上</li>
              <li>应该会在右侧弹出对应的二级菜单</li>
              <li>可以点击二级菜单项进行导航</li>
              <li>鼠标离开后菜单会自动隐藏</li>
            </ul>
          </div>
          
          {/* 功能特性说明 */}
          <div>
            <h3>功能特性:</h3>
            <ul>
              <li><strong>响应式设计</strong>: 侧边栏在不同屏幕尺寸下自适应</li>
              <li><strong>悬浮菜单</strong>: 收起状态下鼠标悬停显示完整菜单</li>
              <li><strong>平滑动画</strong>: 展开/收起过程有流畅的过渡效果</li>
              <li><strong>状态持久化</strong>: 侧边栏状态会保存到本地存储</li>
              <li><strong>键盘导航</strong>: 支持键盘快捷键操作</li>
            </ul>
          </div>
        </Space>
      </div>
    </div>
  );
};

export default SidebarTest;