/**
 * 侧边栏组件 - 支持二级菜单结构
 */

import React, { useState, useEffect } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  UserOutlined,
  LineChartOutlined,
  BankOutlined,
  BarChartOutlined,
  SettingOutlined,
  TeamOutlined,
  SafetyOutlined,
  WalletOutlined,
  GoldOutlined,
  UnorderedListOutlined,
  FolderOutlined,
  HistoryOutlined,
  AppstoreOutlined,
  ExperimentOutlined,
  EyeOutlined,
  AreaChartOutlined,
  PieChartOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  MenuOutlined,
  DesktopOutlined,
  DatabaseOutlined,
  FileOutlined,
  ControlOutlined,
} from '@ant-design/icons';
import { useAppStore } from '@/store';
import { useResponsive } from '@/hooks';
import classNames from 'classnames';

const { Sider } = Layout;

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isMobile } = useResponsive();
  const { sidebarCollapsed, mobileMenuOpen, setMobileMenuOpen } = useAppStore();
  const [openKeys, setOpenKeys] = useState<string[]>([]);

  // 菜单项配置 - 重新设计的二级菜单结构
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表盘',
    },
    {
      key: 'account',
      icon: <UserOutlined />,
      label: '账户管理',
      children: [
        {
          key: '/account/users',
          icon: <TeamOutlined />,
          label: '用户管理',
        },
        {
          key: '/account/roles',
          icon: <SafetyOutlined />,
          label: '角色权限',
        },
        {
          key: '/account/exchanges',
          icon: <WalletOutlined />,
          label: '交易账户',
        },
      ],
    },
    {
      key: 'trading',
      icon: <LineChartOutlined />,
      label: '交易中心',
      children: [
        {
          key: '/trading/spot',
          icon: <GoldOutlined />,
          label: '现货交易',
        },
        {
          key: '/trading/orders',
          icon: <UnorderedListOutlined />,
          label: '订单管理',
        },
        {
          key: '/trading/positions',
          icon: <FolderOutlined />,
          label: '持仓管理',
        },
        {
          key: '/trading/history',
          icon: <HistoryOutlined />,
          label: '交易历史',
        },
      ],
    },
    {
      key: 'strategy',
      icon: <BankOutlined />,
      label: '策略管理',
      children: [
        {
          key: '/strategy/list',
          icon: <AppstoreOutlined />,
          label: '策略列表',
        },
        {
          key: '/strategy/backtest',
          icon: <ExperimentOutlined />,
          label: '策略回测',
        },
        {
          key: '/strategy/monitor',
          icon: <EyeOutlined />,
          label: '策略监控',
        },
        {
          key: '/strategy/risk',
          icon: <SafetyOutlined />,
          label: '风险控制',
        },
      ],
    },
    {
      key: 'analysis',
      icon: <BarChartOutlined />,
      label: '数据分析',
      children: [
        {
          key: '/analysis/market',
          icon: <AreaChartOutlined />,
          label: '市场行情',
        },
        {
          key: '/analysis/performance',
          icon: <PieChartOutlined />,
          label: '收益分析',
        },
        {
          key: '/analysis/risk',
          icon: <ExclamationCircleOutlined />,
          label: '风险分析',
        },
        {
          key: '/analysis/reports',
          icon: <FileTextOutlined />,
          label: '报表中心',
        },
      ],
    },
    {
      key: 'system',
      icon: <SettingOutlined />,
      label: '系统设置',
      children: [
        {
          key: '/system/menus',
          icon: <MenuOutlined />,
          label: '菜单管理',
        },
        {
          key: '/system/monitor',
          icon: <DesktopOutlined />,
          label: '系统监控',
        },
        {
          key: '/system/database',
          icon: <DatabaseOutlined />,
          label: '数据库管理',
        },
        {
          key: '/system/logs',
          icon: <FileOutlined />,
          label: '系统日志',
        },
        {
          key: '/system/config',
          icon: <ControlOutlined />,
          label: '系统配置',
        },
      ],
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

  // 处理子菜单展开/收起
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  // 根据当前路径设置选中的菜单项和展开的子菜单
  useEffect(() => {
    const pathname = location.pathname;
    
    // 查找匹配的菜单项
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (pathname.startsWith(child.key)) {
            // 如果当前路径匹配子菜单，展开对应的父菜单
            if (!openKeys.includes(item.key)) {
              setOpenKeys([...openKeys, item.key]);
            }
            break;
          }
        }
      }
    }
  }, [location.pathname]);

  // 获取当前选中的菜单项
  const getSelectedKeys = () => {
    const pathname = location.pathname;
    
    // 精确匹配
    for (const item of menuItems) {
      if (item.key === pathname) {
        return [pathname];
      }
      if (item.children) {
        for (const child of item.children) {
          if (child.key === pathname) {
            return [pathname];
          }
        }
      }
    }
    
    // 前缀匹配
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (pathname.startsWith(child.key)) {
            return [child.key];
          }
        }
      }
    }
    
    return [pathname];
  };

  const selectedKeys = getSelectedKeys();

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
        openKeys={sidebarCollapsed && !isMobile ? [] : openKeys}
        items={menuItems}
        onClick={handleMenuClick}
        onOpenChange={handleOpenChange}
        className="sidebar-menu"
        inlineCollapsed={sidebarCollapsed && !isMobile}
      />
    </Sider>
  );
};

export default Sidebar;