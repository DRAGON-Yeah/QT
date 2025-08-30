import React, { useState, useEffect } from 'react';
import { Card, Menu, Tabs, Switch, Space, Divider } from 'antd';
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined,
  DesktopOutlined,
  TabletOutlined,
  MobileOutlined
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import './MenuPreview.scss';

const { TabPane } = Tabs;
const { SubMenu } = Menu;

interface MenuPreviewProps {
  menuTree: any[];
  onMenuUpdate?: () => void;
}

type MenuItem = Required<MenuProps>['items'][number];

const MenuPreview: React.FC<MenuPreviewProps> = ({ menuTree, onMenuUpdate }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [mode, setMode] = useState<'vertical' | 'horizontal'>('vertical');
  const [deviceType, setDeviceType] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // 转换菜单数据为Antd Menu组件需要的格式
  const convertToMenuItems = (nodes: any[]): MenuItem[] => {
    return nodes
      .filter(node => node.is_visible && node.is_enabled)
      .map(node => {
        const item: MenuItem = {
          key: node.id,
          icon: node.icon ? <i className={node.icon} /> : undefined,
          label: node.title,
        };

        if (node.children && node.children.length > 0) {
          const children = convertToMenuItems(node.children);
          if (children.length > 0) {
            return {
              ...item,
              children,
              type: 'group'
            };
          }
        }

        return item;
      });
  };

  const menuItems = convertToMenuItems(menuTree);

  // 监听菜单数据变化，自动刷新预览
  useEffect(() => {
    if (autoRefresh && onMenuUpdate) {
      // 这里可以添加自动刷新逻辑
      // 例如定时检查菜单数据是否有变化
    }
  }, [menuTree, autoRefresh, onMenuUpdate]);

  // 获取设备样式类
  const getDeviceClass = () => {
    switch (deviceType) {
      case 'tablet':
        return 'preview-tablet';
      case 'mobile':
        return 'preview-mobile';
      default:
        return 'preview-desktop';
    }
  };

  return (
    <div className="menu-preview">
      <div className="preview-controls">
        <Space split={<Divider type="vertical" />}>
          <Space>
            <span>设备类型：</span>
            <Space>
              <DesktopOutlined
                className={deviceType === 'desktop' ? 'active' : ''}
                onClick={() => setDeviceType('desktop')}
              />
              <TabletOutlined
                className={deviceType === 'tablet' ? 'active' : ''}
                onClick={() => setDeviceType('tablet')}
              />
              <MobileOutlined
                className={deviceType === 'mobile' ? 'active' : ''}
                onClick={() => setDeviceType('mobile')}
              />
            </Space>
          </Space>

          <Space>
            <span>主题：</span>
            <Switch
              checked={theme === 'dark'}
              onChange={(checked) => setTheme(checked ? 'dark' : 'light')}
              checkedChildren="暗色"
              unCheckedChildren="亮色"
            />
          </Space>

          <Space>
            <span>模式：</span>
            <Switch
              checked={mode === 'horizontal'}
              onChange={(checked) => setMode(checked ? 'horizontal' : 'vertical')}
              checkedChildren="水平"
              unCheckedChildren="垂直"
            />
          </Space>

          {mode === 'vertical' && (
            <Space>
              <span>折叠：</span>
              <Switch
                checked={collapsed}
                onChange={setCollapsed}
                checkedChildren={<MenuFoldOutlined />}
                unCheckedChildren={<MenuUnfoldOutlined />}
              />
            </Space>
          )}

          <Space>
            <span>实时预览：</span>
            <Switch
              checked={autoRefresh}
              onChange={setAutoRefresh}
              checkedChildren="开启"
              unCheckedChildren="关闭"
            />
          </Space>
        </Space>
      </div>

      <div className={`preview-container ${getDeviceClass()}`}>
        <Tabs defaultActiveKey="sidebar" className="preview-tabs">
          <TabPane tab="侧边栏菜单" key="sidebar">
            <div className="sidebar-preview">
              <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                <div className="sidebar-header">
                  <div className="logo">
                    {collapsed ? 'Q' : 'QuantTrade'}
                  </div>
                </div>
                <Menu
                  theme={theme}
                  mode="inline"
                  inlineCollapsed={collapsed}
                  items={menuItems}
                  className="sidebar-menu"
                />
              </div>
              <div className="content-area">
                <div className="content-placeholder">
                  <h3>内容区域</h3>
                  <p>这里是页面内容区域</p>
                </div>
              </div>
            </div>
          </TabPane>

          <TabPane tab="顶部菜单" key="header">
            <div className="header-preview">
              <div className="header">
                <div className="header-left">
                  <div className="logo">QuantTrade</div>
                </div>
                <div className="header-menu">
                  <Menu
                    theme={theme}
                    mode="horizontal"
                    items={menuItems}
                    className="header-menu-items"
                  />
                </div>
                <div className="header-right">
                  <span>用户区域</span>
                </div>
              </div>
              <div className="content-area">
                <div className="content-placeholder">
                  <h3>内容区域</h3>
                  <p>这里是页面内容区域</p>
                </div>
              </div>
            </div>
          </TabPane>

          <TabPane tab="混合菜单" key="mixed">
            <div className="mixed-preview">
              <div className="header">
                <div className="header-left">
                  <div className="logo">QuantTrade</div>
                </div>
                <div className="header-menu">
                  <Menu
                    theme={theme}
                    mode="horizontal"
                    items={menuItems.slice(0, 3)} // 只显示前3个主菜单
                    className="header-menu-items"
                  />
                </div>
                <div className="header-right">
                  <span>用户区域</span>
                </div>
              </div>
              <div className="body">
                <div className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
                  <Menu
                    theme={theme}
                    mode="inline"
                    inlineCollapsed={collapsed}
                    items={menuItems.slice(3)} // 显示剩余菜单
                    className="sidebar-menu"
                  />
                </div>
                <div className="content-area">
                  <div className="content-placeholder">
                    <h3>内容区域</h3>
                    <p>这里是页面内容区域</p>
                  </div>
                </div>
              </div>
            </div>
          </TabPane>
        </Tabs>
      </div>
    </div>
  );
};

export default MenuPreview;