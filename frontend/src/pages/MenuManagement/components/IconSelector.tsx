import React, { useState, useEffect } from 'react';
import { Modal, Tabs, Input, Row, Col, Card, Empty, Spin } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { menuService } from '../../../services/menuService';
import './IconSelector.scss';

const { TabPane } = Tabs;
const { Search } = Input;

interface IconSelectorProps {
  visible: boolean;
  onSelect: (icon: string) => void;
  onCancel: () => void;
}

interface IconItem {
  name: string;
  class: string;
  unicode: string;
}

interface IconCategory {
  [key: string]: IconItem[];
}

const IconSelector: React.FC<IconSelectorProps> = ({
  visible,
  onSelect,
  onCancel
}) => {
  const [icons, setIcons] = useState<IconCategory>({});
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [activeTab, setActiveTab] = useState('common');

  // 加载图标数据
  useEffect(() => {
    if (visible) {
      loadIcons();
    }
  }, [visible]);

  const loadIcons = async () => {
    setLoading(true);
    try {
      const response = await menuService.getIcons();
      setIcons(response.data);
    } catch (error) {
      console.error('加载图标失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 过滤图标
  const filterIcons = (iconList: IconItem[]) => {
    if (!searchText) return iconList;
    
    return iconList.filter(icon =>
      icon.name.toLowerCase().includes(searchText.toLowerCase()) ||
      icon.class.toLowerCase().includes(searchText.toLowerCase())
    );
  };

  // 处理图标选择
  const handleIconSelect = (icon: IconItem) => {
    onSelect(icon.class);
  };

  return (
    <Modal
      title="选择图标"
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      className="icon-selector-modal"
    >
      <div className="icon-selector">
        <div className="search-bar">
          <Search
            placeholder="搜索图标..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            prefix={<SearchOutlined />}
            allowClear
          />
        </div>

        <Spin spinning={loading}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            className="icon-tabs"
          >
            {Object.entries(icons).map(([category, iconList]) => (
              <TabPane
                tab={getCategoryName(category)}
                key={category}
              >
                <div className="icon-grid">
                  {filterIcons(iconList).length > 0 ? (
                    <Row gutter={[8, 8]}>
                      {filterIcons(iconList).map((icon) => (
                        <Col span={4} key={icon.name}>
                          <Card
                            hoverable
                            className="icon-card"
                            onClick={() => handleIconSelect(icon)}
                            bodyStyle={{ padding: '12px' }}
                          >
                            <div className="icon-content">
                              <i className={icon.class} />
                              <div className="icon-name">{icon.name}</div>
                            </div>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  ) : (
                    <Empty description="没有找到匹配的图标" />
                  )}
                </div>
              </TabPane>
            ))}
          </Tabs>
        </Spin>
      </div>
    </Modal>
  );
};

// 获取分类名称
const getCategoryName = (category: string): string => {
  const categoryNames: { [key: string]: string } = {
    common: '常用图标',
    trading: '交易图标',
    system: '系统图标'
  };
  return categoryNames[category] || category;
};

export default IconSelector;