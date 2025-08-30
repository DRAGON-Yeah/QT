/**
 * 侧边栏组件 - 支持二级菜单结构
 */

import React, { useState, useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  UserOutlined,
  LineChartOutlined,
  FundOutlined,
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
  // 悬浮子菜单相关状态
  const [hoveredSubmenu, setHoveredSubmenu] = useState<string | null>(null); // 当前悬浮显示的子菜单key
  const [submenuPosition, setSubmenuPosition] = useState({ top: 0, left: 0 }); // 悬浮子菜单的位置
  const submenuRef = useRef<HTMLDivElement>(null); // 悬浮子菜单的DOM引用
  const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null); // 悬浮延迟隐藏的定时器

  // 菜单项配置 - 完整的二级菜单结构
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
      icon: <FundOutlined />,
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
    // 在折叠状态下，如果点击的是父菜单key且有子菜单，则导航到第一个子菜单
    if (sidebarCollapsed && !isMobile) {
      const parentMenu = menuItems.find(item => item.key === key && item.children);
      if (parentMenu && parentMenu.children && parentMenu.children.length > 0) {
        navigate(parentMenu.children[0].key);
      } else {
        navigate(key);
      }
    } else {
      navigate(key);
    }
    
    // 移动端点击菜单后关闭侧边栏
    if (isMobile) {
      setMobileMenuOpen(false);
    }
    // 隐藏悬浮菜单
    setHoveredSubmenu(null);
  };

  // 处理子菜单展开/收起
  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys);
  };

  /**
   * 处理鼠标悬停在一级菜单上的事件
   * 仅在侧边栏折叠且非移动端时生效
   * @param e - 鼠标事件对象
   * @param menuKey - 菜单项的key
   */
  const handleMenuItemHover = (e: React.MouseEvent, menuKey: string) => {
    // 只在折叠状态且非移动端时显示悬浮菜单
    if (!sidebarCollapsed || isMobile) return;

    // 查找对应的菜单项，确保有子菜单
    const menuItem = menuItems.find(item => item.key === menuKey);
    if (!menuItem || !menuItem.children) return;

    // 清除之前的延迟隐藏定时器
    if (hoverTimeoutRef.current) {
      clearTimeout(hoverTimeoutRef.current);
    }

    // 计算悬浮菜单的显示位置
    const rect = e.currentTarget.getBoundingClientRect();
    setSubmenuPosition({
      top: rect.top,
      left: rect.right + 4, // 在菜单项右侧4px处显示，减少间距
    });
    setHoveredSubmenu(menuKey);
  };

  /**
   * 处理鼠标离开一级菜单的事件
   * 不自动隐藏悬浮菜单，只有点击才隐藏
   */
  const handleMenuItemLeave = () => {
    // 不再自动隐藏悬浮菜单
    // 悬浮菜单只有在点击时才隐藏
  };

  /**
   * 处理鼠标进入悬浮子菜单的事件
   * 保持子菜单显示
   */
  const handleSubmenuEnter = () => {
    // 悬浮菜单不再自动隐藏，无需处理定时器
  };

  /**
   * 处理鼠标离开悬浮子菜单的事件
   * 不自动隐藏，只有点击才隐藏
   */
  const handleSubmenuLeave = () => {
    // 不再自动隐藏悬浮菜单
    // 悬浮菜单只有在点击时才隐藏
  };

  // 点击外部区域隐藏悬浮菜单
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      // 检查点击是否在侧边栏或悬浮菜单外部
      if (!target.closest('.sidebar') && !target.closest('.floating-submenu')) {
        setHoveredSubmenu(null);
      }
    };

    if (hoveredSubmenu) {
      document.addEventListener('click', handleClickOutside);
    }

    return () => {
      document.removeEventListener('click', handleClickOutside);
      if (hoverTimeoutRef.current) {
        clearTimeout(hoverTimeoutRef.current);
      }
    };
  }, [hoveredSubmenu]);

  /**
   * 根据当前路径自动展开对应的父菜单
   * 确保用户能看到当前页面在菜单中的位置
   */
  useEffect(() => {
    const pathname = location.pathname;

    // 遍历所有菜单项，查找匹配的子菜单
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
  }, [location.pathname, openKeys]);

  /**
   * 获取当前选中的菜单项
   * 支持精确匹配和前缀匹配两种模式
   * @returns 选中的菜单项key数组
   */
  const getSelectedKeys = () => {
    const pathname = location.pathname;

    // 第一轮：精确匹配
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

    // 第二轮：前缀匹配（用于动态路由）
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (pathname.startsWith(child.key)) {
            return [child.key];
          }
        }
      }
    }

    // 默认返回当前路径
    return [pathname];
  };

  const selectedKeys = getSelectedKeys();

  const siderClass = classNames('app-sidebar', {
    'app-sidebar--collapsed': sidebarCollapsed && !isMobile,
    'app-sidebar--mobile': isMobile,
    'app-sidebar--mobile-open': isMobile && mobileMenuOpen,
  });

  /**
   * 增强菜单项配置，添加折叠状态下的悬停事件
   * 在折叠状态下有子菜单的项目会显示悬浮菜单
   */
  const enhancedMenuItems = menuItems.map(item => {
    if (item.children) {
      // 有子菜单的菜单项，添加悬停事件
      return {
        ...item,
        // 在菜单项上添加悬停事件处理
        onMouseEnter: (info: { key: string; domEvent: React.MouseEvent<HTMLElement> }) => {
          if (sidebarCollapsed && !isMobile) {
            handleMenuItemHover(info.domEvent, item.key);
          }
        },
        onMouseLeave: () => {
          if (sidebarCollapsed && !isMobile) {
            handleMenuItemLeave();
          }
        },
      };
    }
    // 没有子菜单的菜单项保持原样
    return item;
  });

  return (
    <>
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
        <div
          className="sidebar-menu-wrapper"
          onMouseLeave={() => {
            if (sidebarCollapsed && !isMobile) {
              handleMenuItemLeave();
            }
          }}
        >
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={selectedKeys}
            openKeys={sidebarCollapsed && !isMobile ? [] : openKeys}
            items={enhancedMenuItems}
            onClick={handleMenuClick}
            onOpenChange={handleOpenChange}
            className={classNames('sidebar-menu', {
              'sidebar-menu--collapsed': sidebarCollapsed && !isMobile
            })}
            inlineCollapsed={sidebarCollapsed && !isMobile}
          />


        </div>
      </Sider>

      {/* 悬浮子菜单通过Portal渲染到document.body，避免影响其他元素布局 */}
      {hoveredSubmenu && sidebarCollapsed && !isMobile && ReactDOM.createPortal(
        <div
          ref={submenuRef}
          className="sidebar-floating-submenu"
          style={{
            position: 'fixed',
            top: submenuPosition.top,
            left: submenuPosition.left,
            zIndex: 9999,
          }}
          onMouseEnter={handleSubmenuEnter}
          onMouseLeave={handleSubmenuLeave}
        >
          <div className="floating-submenu-content">
            <div className="floating-submenu-title">
              {menuItems.find(item => item.key === hoveredSubmenu)?.label}
            </div>
            <div className="floating-submenu-items">
              {menuItems
                .find(item => item.key === hoveredSubmenu)
                ?.children?.map(child => (
                  <div
                    key={child.key}
                    className={classNames('floating-submenu-item', {
                      'floating-submenu-item--active': selectedKeys.includes(child.key)
                    })}
                    onClick={() => {
                      // 点击子菜单项后立即隐藏悬浮菜单
                      setHoveredSubmenu(null);
                      // 导航到选中的菜单
                      handleMenuClick({ key: child.key });
                    }}
                  >
                    <span className="floating-submenu-item-icon">{child.icon}</span>
                    <span className="floating-submenu-item-label">{child.label}</span>
                  </div>
                ))}
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
};

export default Sidebar;