import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Switch, Button, TreeSelect, Space, Row, Col, Divider } from 'antd';
import { SaveOutlined, CloseOutlined } from '@ant-design/icons';
import IconSelector from './IconSelector';
import { menuService } from '../../../services/menuService';

const { Option } = Select;
const { TextArea } = Input;

interface MenuFormProps {
  mode: 'create' | 'edit';
  initialValues?: any;
  onSubmit: (values: any) => void;
  onCancel: () => void;
}

const MenuForm: React.FC<MenuFormProps> = ({
  mode,
  initialValues,
  onSubmit,
  onCancel
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [menuTree, setMenuTree] = useState([]);
  const [permissions, setPermissions] = useState([]);
  const [roles, setRoles] = useState([]);
  const [iconSelectorVisible, setIconSelectorVisible] = useState(false);

  // 加载数据
  useEffect(() => {
    loadFormData();
  }, []);

  // 设置初始值
  useEffect(() => {
    if (initialValues) {
      const formValues = {
        ...initialValues,
        parent_id: initialValues.parent_id || undefined,
        permissions: initialValues.permissions || [],
        roles: initialValues.roles || [],
        is_visible: initialValues.is_visible !== false,
        is_enabled: initialValues.is_enabled !== false,
        is_cache: initialValues.is_cache !== false,
      };
      form.setFieldsValue(formValues);
    }
  }, [initialValues, form]);

  const loadFormData = async () => {
    try {
      const [menuResponse, permissionsResponse, rolesResponse] = await Promise.all([
        menuService.getMenuTree(),
        menuService.getPermissions(),
        menuService.getRoles()
      ]);

      setMenuTree(convertToTreeSelectData(menuResponse.data));
      setPermissions(permissionsResponse.data);
      setRoles(rolesResponse.data);
    } catch (error) {
      console.error('加载表单数据失败:', error);
    }
  };

  // 转换为TreeSelect需要的数据格式
  const convertToTreeSelectData = (nodes: any[]): any[] => {
    return nodes.map(node => ({
      title: node.title,
      value: node.id,
      key: node.id,
      children: node.children ? convertToTreeSelectData(node.children) : undefined,
      disabled: mode === 'edit' && initialValues && node.id === initialValues.id // 禁止选择自己作为父菜单
    }));
  };

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // 处理表单数据
      const submitData = {
        ...values,
        meta_info: values.meta_info ? JSON.parse(values.meta_info) : {}
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error('提交失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleIconSelect = (icon: string) => {
    form.setFieldsValue({ icon });
    setIconSelectorVisible(false);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        menu_type: 'menu',
        target: '_self',
        sort_order: 0,
        is_visible: true,
        is_enabled: true,
        is_cache: true
      }}
    >
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="name"
            label="菜单名称"
            rules={[
              { required: true, message: '请输入菜单名称' },
              { pattern: /^[a-zA-Z][a-zA-Z0-9_]*$/, message: '菜单名称只能包含字母、数字和下划线，且必须以字母开头' }
            ]}
          >
            <Input placeholder="请输入菜单名称（英文）" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="title"
            label="显示标题"
            rules={[{ required: true, message: '请输入显示标题' }]}
          >
            <Input placeholder="请输入显示标题（中文）" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="icon" label="图标">
            <Input
              placeholder="请选择图标"
              suffix={
                <Button
                  type="link"
                  size="small"
                  onClick={() => setIconSelectorVisible(true)}
                >
                  选择图标
                </Button>
              }
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="parent_id" label="父菜单">
            <TreeSelect
              placeholder="请选择父菜单（不选择则为根菜单）"
              allowClear
              treeData={menuTree}
              treeDefaultExpandAll
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="path" label="路由路径">
            <Input placeholder="请输入路由路径，如：/dashboard" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="component" label="组件路径">
            <Input placeholder="请输入组件路径，如：Dashboard/index" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="menu_type" label="菜单类型">
            <Select>
              <Option value="menu">菜单</Option>
              <Option value="button">按钮</Option>
              <Option value="link">链接</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="target" label="打开方式">
            <Select>
              <Option value="_self">当前窗口</Option>
              <Option value="_blank">新窗口</Option>
            </Select>
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="sort_order" label="排序">
            <Input type="number" placeholder="数字越小越靠前" />
          </Form.Item>
        </Col>
      </Row>

      <Divider>权限配置</Divider>

      <Row gutter={16}>
        <Col span={12}>
          <Form.Item name="permissions" label="所需权限">
            <Select
              mode="multiple"
              placeholder="请选择所需权限"
              allowClear
              showSearch
              filterOption={(input, option) =>
                (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {permissions.map((perm: any) => (
                <Option key={perm.id} value={perm.id}>
                  {perm.name} ({perm.codename})
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item name="roles" label="可访问角色">
            <Select
              mode="multiple"
              placeholder="请选择可访问角色"
              allowClear
            >
              {roles.map((role: any) => (
                <Option key={role.id} value={role.id}>
                  {role.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Col>
      </Row>

      <Divider>显示配置</Divider>

      <Row gutter={16}>
        <Col span={8}>
          <Form.Item name="is_visible" label="是否显示" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="is_enabled" label="是否启用" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
        <Col span={8}>
          <Form.Item name="is_cache" label="是否缓存" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="meta_info" label="扩展配置">
        <TextArea
          rows={4}
          placeholder="请输入JSON格式的扩展配置，如：{&quot;keepAlive&quot;: true}"
        />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            icon={<SaveOutlined />}
          >
            {mode === 'create' ? '创建' : '更新'}
          </Button>
          <Button onClick={onCancel} icon={<CloseOutlined />}>
            取消
          </Button>
        </Space>
      </Form.Item>

      {/* 图标选择器 */}
      <IconSelector
        visible={iconSelectorVisible}
        onSelect={handleIconSelect}
        onCancel={() => setIconSelectorVisible(false)}
      />
    </Form>
  );
};

export default MenuForm;