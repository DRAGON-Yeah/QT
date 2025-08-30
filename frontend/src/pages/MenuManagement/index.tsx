import React, { useState, useEffect, useRef } from 'react';
import { Card, Button, Tree, Form, Input, Select, Switch, Modal, message, Space, Tooltip } from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined, 
  EyeInvisibleOutlined,
  DragOutlined,
  SettingOutlined,
  MenuOutlined,
  SaveOutlined,
  DownloadOutlined,
  UploadOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import type { TreeDataNode, TreeProps } from 'antd';
import MenuForm from './components/MenuForm';
import MenuPreview from './components/MenuPreview';
import IconSelector from './components/IconSelector';
import MenuImport from './components/MenuImport';
import { menuService } from '../../services/menuService';
import './style.scss';

const { Option } = Select;

interface MenuNode {
  id: number;
  name: string;
  title: string;
  icon: string;
  path: string;
  component: string;
  menu_type: string;
  target: string;
  level: number;
  sort_order: number;
  is_visible: boolean;
  is_enabled: boolean;
  parent_id?: number;
  children?: MenuNode[];
  permissions?: number[];
  roles?: number[];
  meta?: any;
}

const MenuManagement: React.FC = () => {
  const [menuTree, setMenuTree] = useState<MenuNode[]>([]);
  const [selectedMenu, setSelectedMenu] = useState<MenuNode | null>(null);
  const [isFormVisible, setIsFormVisible] = useState(false);
  const [isPreviewVisible, setIsPreviewVisible] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [loading, setLoading] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<React.Key[]>([]);
  const [dragEnabled, setDragEnabled] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [isConfigVisible, setIsConfigVisible] = useState(false);
  const [isImportVisible, setIsImportVisible] = useState(false);
  const draggedNodeRef = useRef<MenuNode | null>(null);

  // 加载菜单树
  const loadMenuTree = async () => {
    setLoading(true);
    try {
      const response = await menuService.getMenuTree();
      setMenuTree(response.data);
      
      // 默认展开所有节点
      const allKeys = getAllKeys(response.data);
      setExpandedKeys(allKeys);
    } catch (error) {
      message.error('加载菜单失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取所有节点的key
  const getAllKeys = (nodes: MenuNode[]): React.Key[] => {
    const keys: React.Key[] = [];
    const traverse = (items: MenuNode[]) => {
      items.forEach(item => {
        keys.push(item.id);
        if (item.children && item.children.length > 0) {
          traverse(item.children);
        }
      });
    };
    traverse(nodes);
    return keys;
  };

  // 转换为Tree组件需要的数据格式
  const convertToTreeData = (nodes: MenuNode[]): TreeDataNode[] => {
    return nodes.map(node => ({
      key: node.id,
      title: (
        <div className="menu-tree-node">
          <div className="menu-info">
            {node.icon && <i className={node.icon} />}
            <span className="menu-title">{node.title}</span>
            <span className="menu-name">({node.name})</span>
          </div>
          <div className="menu-actions">
            {!dragEnabled && (
              <>
                <Tooltip title={node.is_visible ? '隐藏' : '显示'}>
                  <Button
                    type="text"
                    size="small"
                    icon={node.is_visible ? <EyeOutlined /> : <EyeInvisibleOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleVisibility(node);
                    }}
                  />
                </Tooltip>
                <Tooltip title="编辑">
                  <Button
                    type="text"
                    size="small"
                    icon={<EditOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(node);
                    }}
                  />
                </Tooltip>
                <Tooltip title="添加子菜单">
                  <Button
                    type="text"
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAddChild(node);
                    }}
                  />
                </Tooltip>
                <Tooltip title="删除">
                  <Button
                    type="text"
                    size="small"
                    danger
                    icon={<DeleteOutlined />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(node);
                    }}
                  />
                </Tooltip>
              </>
            )}
            {dragEnabled && (
              <Tooltip title="拖拽移动">
                <DragOutlined className="drag-handle" />
              </Tooltip>
            )}
          </div>
        </div>
      ),
      children: node.children ? convertToTreeData(node.children) : undefined,
      className: `menu-node ${!node.is_visible ? 'menu-hidden' : ''} ${!node.is_enabled ? 'menu-disabled' : ''}`
    }));
  };

  // 切换菜单可见性
  const toggleVisibility = async (menu: MenuNode) => {
    try {
      await menuService.toggleVisibility(menu.id);
      message.success(`菜单已${menu.is_visible ? '隐藏' : '显示'}`);
      loadMenuTree();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 处理编辑
  const handleEdit = (menu: MenuNode) => {
    setSelectedMenu(menu);
    setFormMode('edit');
    setIsFormVisible(true);
  };

  // 处理添加子菜单
  const handleAddChild = (parentMenu: MenuNode) => {
    setSelectedMenu({ ...parentMenu, id: 0, parent_id: parentMenu.id } as MenuNode);
    setFormMode('create');
    setIsFormVisible(true);
  };

  // 处理删除
  const handleDelete = (menu: MenuNode) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除菜单"${menu.title}"吗？`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await menuService.deleteMenu(menu.id);
          message.success('删除成功');
          loadMenuTree();
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 处理表单提交
  const handleFormSubmit = async (values: any) => {
    try {
      if (formMode === 'create') {
        await menuService.createMenu(values);
        message.success('创建成功');
      } else {
        await menuService.updateMenu(selectedMenu!.id, values);
        message.success('更新成功');
      }
      setIsFormVisible(false);
      loadMenuTree();
    } catch (error) {
      message.error('操作失败');
    }
  };

  // 处理树节点选择
  const handleTreeSelect = (selectedKeys: React.Key[], info: any) => {
    setSelectedKeys(selectedKeys);
    if (selectedKeys.length > 0) {
      const menuId = selectedKeys[0] as number;
      const menu = findMenuById(menuTree, menuId);
      setSelectedMenu(menu);
    } else {
      setSelectedMenu(null);
    }
  };

  // 根据ID查找菜单
  const findMenuById = (nodes: MenuNode[], id: number): MenuNode | null => {
    for (const node of nodes) {
      if (node.id === id) {
        return node;
      }
      if (node.children) {
        const found = findMenuById(node.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  // 处理拖拽开始
  const handleDragStart = (info: any) => {
    const { node } = info;
    draggedNodeRef.current = findMenuById(menuTree, node.key);
  };

  // 处理拖拽结束
  const handleDrop = (info: any) => {
    const { node, dragNode, dropPosition, dropToGap } = info;
    
    if (!draggedNodeRef.current) return;

    const draggedMenu = draggedNodeRef.current;
    const targetMenu = findMenuById(menuTree, node.key);
    
    if (!targetMenu || draggedMenu.id === targetMenu.id) return;

    // 防止将父节点拖拽到子节点下
    if (isDescendant(targetMenu, draggedMenu)) {
      message.warning('不能将父菜单拖拽到子菜单下');
      return;
    }

    // 计算新的排序和父级关系
    let newParentId = null;
    let newSortOrder = 0;

    if (!dropToGap) {
      // 拖拽到节点内部，作为子节点
      newParentId = targetMenu.id;
      newSortOrder = (targetMenu.children?.length || 0) + 1;
    } else {
      // 拖拽到节点之间
      newParentId = targetMenu.parent_id || null;
      
      // 计算新的排序位置
      const siblings = getSiblings(menuTree, targetMenu.parent_id);
      const targetIndex = siblings.findIndex(item => item.id === targetMenu.id);
      
      if (dropPosition === -1) {
        // 拖拽到目标节点之前
        newSortOrder = targetMenu.sort_order;
      } else {
        // 拖拽到目标节点之后
        newSortOrder = targetMenu.sort_order + 1;
      }
    }

    // 更新本地状态
    updateMenuTreeAfterDrag(draggedMenu.id, newParentId, newSortOrder);
    setHasChanges(true);
  };

  // 检查是否为子孙节点
  const isDescendant = (ancestor: MenuNode, descendant: MenuNode): boolean => {
    const checkChildren = (node: MenuNode): boolean => {
      if (node.id === ancestor.id) return true;
      if (node.children) {
        return node.children.some(child => checkChildren(child));
      }
      return false;
    };
    
    return checkChildren(descendant);
  };

  // 获取同级菜单
  const getSiblings = (nodes: MenuNode[], parentId: number | null | undefined): MenuNode[] => {
    if (parentId === null || parentId === undefined) {
      return nodes.filter(node => !node.parent_id);
    }
    
    const parent = findMenuById(nodes, parentId);
    return parent?.children || [];
  };

  // 更新菜单树结构（拖拽后）
  const updateMenuTreeAfterDrag = (draggedId: number, newParentId: number | null, newSortOrder: number) => {
    const updateTree = (nodes: MenuNode[]): MenuNode[] => {
      return nodes.map(node => {
        if (node.id === draggedId) {
          // 更新被拖拽的节点
          return {
            ...node,
            parent_id: newParentId,
            sort_order: newSortOrder,
            level: newParentId ? (findMenuById(menuTree, newParentId)?.level || 0) + 1 : 1
          };
        }
        
        if (node.children) {
          const updatedChildren = updateTree(node.children);
          // 移除被拖拽的子节点
          const filteredChildren = updatedChildren.filter(child => child.id !== draggedId);
          
          // 如果当前节点是新的父节点，添加被拖拽的节点
          if (node.id === newParentId) {
            const draggedNode = findMenuById(menuTree, draggedId);
            if (draggedNode) {
              filteredChildren.push({
                ...draggedNode,
                parent_id: newParentId,
                sort_order: newSortOrder,
                level: node.level + 1
              });
              // 重新排序
              filteredChildren.sort((a, b) => a.sort_order - b.sort_order);
            }
          }
          
          return { ...node, children: filteredChildren };
        }
        
        return node;
      });
    };

    let updatedTree = updateTree(menuTree);
    
    // 如果拖拽到根级别，需要特殊处理
    if (newParentId === null) {
      const draggedNode = findMenuById(menuTree, draggedId);
      if (draggedNode) {
        // 从原位置移除
        updatedTree = removeNodeFromTree(updatedTree, draggedId);
        // 添加到根级别
        updatedTree.push({
          ...draggedNode,
          parent_id: null,
          sort_order: newSortOrder,
          level: 1
        });
        // 重新排序
        updatedTree.sort((a, b) => a.sort_order - b.sort_order);
      }
    }

    setMenuTree(updatedTree);
  };

  // 从树中移除节点
  const removeNodeFromTree = (nodes: MenuNode[], nodeId: number): MenuNode[] => {
    return nodes.filter(node => {
      if (node.id === nodeId) {
        return false;
      }
      if (node.children) {
        node.children = removeNodeFromTree(node.children, nodeId);
      }
      return true;
    });
  };

  // 保存拖拽排序
  const saveDragChanges = async () => {
    try {
      const menuOrders = collectMenuOrders(menuTree);
      await menuService.reorderMenus(menuOrders);
      message.success('菜单排序保存成功');
      setHasChanges(false);
      loadMenuTree(); // 重新加载以确保数据一致性
    } catch (error) {
      message.error('保存排序失败');
    }
  };

  // 收集菜单排序数据
  const collectMenuOrders = (nodes: MenuNode[], parentId: number | null = null): Array<{id: number, sort_order: number, parent_id?: number}> => {
    const orders: Array<{id: number, sort_order: number, parent_id?: number}> = [];
    
    nodes.forEach((node, index) => {
      orders.push({
        id: node.id,
        sort_order: index + 1,
        parent_id: parentId || undefined
      });
      
      if (node.children && node.children.length > 0) {
        orders.push(...collectMenuOrders(node.children, node.id));
      }
    });
    
    return orders;
  };

  // 取消拖拽更改
  const cancelDragChanges = () => {
    setHasChanges(false);
    loadMenuTree();
  };

  // 导出菜单配置
  const handleExport = async () => {
    try {
      const response = await menuService.exportMenus();
      
      // 创建下载链接
      const blob = new Blob([response.data], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // 从响应头获取文件名，或使用默认文件名
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'menus_export.json';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      }
      
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('菜单配置导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };

  // 导入菜单配置
  const handleImport = () => {
    setIsImportVisible(true);
  };

  // 预热缓存
  const handleWarmCache = async () => {
    try {
      await menuService.warmCache();
      message.success('缓存预热完成');
    } catch (error) {
      message.error('缓存预热失败');
    }
  };

  useEffect(() => {
    loadMenuTree();
  }, []);

  return (
    <div className="menu-management">
      <div className="page-header">
        <h1>菜单管理</h1>
        <Space>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setSelectedMenu(null);
              setFormMode('create');
              setIsFormVisible(true);
            }}
            disabled={dragEnabled}
          >
            添加根菜单
          </Button>
          <Button
            icon={<EyeOutlined />}
            onClick={() => setIsPreviewVisible(true)}
            disabled={dragEnabled}
          >
            预览菜单
          </Button>
          <Button
            type={dragEnabled ? 'primary' : 'default'}
            icon={<DragOutlined />}
            onClick={() => {
              if (hasChanges) {
                Modal.confirm({
                  title: '确认操作',
                  content: '当前有未保存的排序更改，是否放弃更改？',
                  onOk: () => {
                    setDragEnabled(!dragEnabled);
                    cancelDragChanges();
                  }
                });
              } else {
                setDragEnabled(!dragEnabled);
              }
            }}
          >
            {dragEnabled ? '退出排序' : '拖拽排序'}
          </Button>
          {dragEnabled && hasChanges && (
            <>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={saveDragChanges}
              >
                保存排序
              </Button>
              <Button
                onClick={cancelDragChanges}
              >
                取消更改
              </Button>
            </>
          )}
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={dragEnabled}
          >
            导出配置
          </Button>
          <Button
            icon={<UploadOutlined />}
            onClick={handleImport}
            disabled={dragEnabled}
          >
            导入配置
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleWarmCache}
            disabled={dragEnabled}
          >
            预热缓存
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setIsConfigVisible(true)}
            disabled={dragEnabled}
          >
            菜单配置
          </Button>
        </Space>
      </div>

      <div className="menu-content">
        <div className="menu-tree-panel">
          <Card title="菜单树" className="tree-card">
            <Tree
              showLine
              showIcon={false}
              expandedKeys={expandedKeys}
              selectedKeys={selectedKeys}
              onExpand={setExpandedKeys}
              onSelect={handleTreeSelect}
              treeData={convertToTreeData(menuTree)}
              loading={loading}
              className={`menu-tree ${dragEnabled ? 'drag-mode' : ''}`}
              draggable={dragEnabled}
              onDragStart={handleDragStart}
              onDrop={handleDrop}
              allowDrop={({ dropNode, dropPosition }) => {
                // 可以根据需要添加拖拽限制逻辑
                return true;
              }}
            />
          </Card>
        </div>

        <div className="menu-config-panel">
          <Card title="菜单配置" className="config-card">
            {selectedMenu ? (
              <div className="menu-details">
                <div className="detail-item">
                  <label>菜单名称：</label>
                  <span>{selectedMenu.name}</span>
                </div>
                <div className="detail-item">
                  <label>显示标题：</label>
                  <span>{selectedMenu.title}</span>
                </div>
                <div className="detail-item">
                  <label>图标：</label>
                  <span>
                    {selectedMenu.icon && <i className={selectedMenu.icon} />}
                    {selectedMenu.icon}
                  </span>
                </div>
                <div className="detail-item">
                  <label>路径：</label>
                  <span>{selectedMenu.path}</span>
                </div>
                <div className="detail-item">
                  <label>组件：</label>
                  <span>{selectedMenu.component}</span>
                </div>
                <div className="detail-item">
                  <label>菜单类型：</label>
                  <span>{selectedMenu.menu_type}</span>
                </div>
                <div className="detail-item">
                  <label>层级：</label>
                  <span>{selectedMenu.level}</span>
                </div>
                <div className="detail-item">
                  <label>排序：</label>
                  <span>{selectedMenu.sort_order}</span>
                </div>
                <div className="detail-item">
                  <label>是否显示：</label>
                  <span>{selectedMenu.is_visible ? '是' : '否'}</span>
                </div>
                <div className="detail-item">
                  <label>是否启用：</label>
                  <span>{selectedMenu.is_enabled ? '是' : '否'}</span>
                </div>

                <div className="detail-actions">
                  <Button
                    type="primary"
                    icon={<EditOutlined />}
                    onClick={() => handleEdit(selectedMenu)}
                  >
                    编辑菜单
                  </Button>
                  <Button
                    icon={<PlusOutlined />}
                    onClick={() => handleAddChild(selectedMenu)}
                  >
                    添加子菜单
                  </Button>
                </div>
              </div>
            ) : (
              <div className="no-selection">
                <p>请选择一个菜单项查看详情</p>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* 菜单表单弹窗 */}
      <Modal
        title={formMode === 'create' ? '添加菜单' : '编辑菜单'}
        open={isFormVisible}
        onCancel={() => setIsFormVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        <MenuForm
          mode={formMode}
          initialValues={selectedMenu}
          onSubmit={handleFormSubmit}
          onCancel={() => setIsFormVisible(false)}
        />
      </Modal>

      {/* 菜单预览弹窗 */}
      <Modal
        title="菜单预览"
        open={isPreviewVisible}
        onCancel={() => setIsPreviewVisible(false)}
        footer={null}
        width={1200}
        destroyOnClose
      >
        <MenuPreview 
          menuTree={menuTree} 
          onMenuUpdate={loadMenuTree}
        />
      </Modal>

      {/* 菜单导入弹窗 */}
      <MenuImport
        visible={isImportVisible}
        onSuccess={() => {
          setIsImportVisible(false);
          loadMenuTree();
        }}
        onCancel={() => setIsImportVisible(false)}
      />
    </div>
  );
};

export default MenuManagement;