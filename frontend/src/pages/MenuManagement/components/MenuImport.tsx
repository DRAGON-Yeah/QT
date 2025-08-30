import React, { useState } from 'react';
import { Modal, Upload, Form, Switch, Button, message, Alert, Space } from 'antd';
import { UploadOutlined, InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { menuService } from '../../../services/menuService';

const { Dragger } = Upload;

interface MenuImportProps {
  visible: boolean;
  onSuccess: () => void;
  onCancel: () => void;
}

const MenuImport: React.FC<MenuImportProps> = ({
  visible,
  onSuccess,
  onCancel
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [fileList, setFileList] = useState<any[]>([]);
  const [previewData, setPreviewData] = useState<any>(null);

  // 文件上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.json',
    fileList,
    beforeUpload: (file) => {
      // 验证文件类型
      const isJson = file.type === 'application/json' || file.name.endsWith('.json');
      if (!isJson) {
        message.error('只能上传JSON格式的文件');
        return false;
      }

      // 验证文件大小（限制为5MB）
      const isLt5M = file.size / 1024 / 1024 < 5;
      if (!isLt5M) {
        message.error('文件大小不能超过5MB');
        return false;
      }

      // 读取文件内容进行预览
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const content = e.target?.result as string;
          const data = JSON.parse(content);
          setPreviewData(data);
        } catch (error) {
          message.error('无效的JSON文件格式');
          setPreviewData(null);
        }
      };
      reader.readAsText(file);

      setFileList([file]);
      return false; // 阻止自动上传
    },
    onRemove: () => {
      setFileList([]);
      setPreviewData(null);
    }
  };

  // 处理导入
  const handleImport = async (values: any) => {
    if (fileList.length === 0) {
      message.error('请选择要导入的文件');
      return;
    }

    setLoading(true);
    try {
      const file = fileList[0];
      const options = {
        clear_existing: values.clear_existing || false,
        update_existing: values.update_existing !== false,
        import_permissions: values.import_permissions || false
      };

      const response = await menuService.importMenus(file, options);
      
      message.success(response.data.message || '导入成功');
      onSuccess();
      handleReset();
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || '导入失败';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 重置表单
  const handleReset = () => {
    form.resetFields();
    setFileList([]);
    setPreviewData(null);
  };

  // 取消导入
  const handleCancel = () => {
    handleReset();
    onCancel();
  };

  return (
    <Modal
      title="导入菜单配置"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={700}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleImport}
        initialValues={{
          update_existing: true,
          clear_existing: false,
          import_permissions: false
        }}
      >
        <Form.Item label="选择文件">
          <Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持JSON格式的菜单配置文件，文件大小不超过5MB
            </p>
          </Dragger>
        </Form.Item>

        {previewData && (
          <Form.Item label="文件预览">
            <Alert
              message="文件信息"
              description={
                <div>
                  <p><strong>版本:</strong> {previewData.version || '未知'}</p>
                  <p><strong>来源租户:</strong> {previewData.tenant || '未知'}</p>
                  <p><strong>导出时间:</strong> {previewData.export_time || '未知'}</p>
                  <p><strong>菜单数量:</strong> {previewData.menus?.length || 0}</p>
                </div>
              }
              type="info"
              showIcon
            />
          </Form.Item>
        )}

        <Form.Item label="导入选项">
          <Space direction="vertical" style={{ width: '100%' }}>
            <Form.Item name="update_existing" valuePropName="checked" noStyle>
              <Switch />
              <span style={{ marginLeft: 8 }}>更新已存在的菜单</span>
            </Form.Item>
            
            <Form.Item name="clear_existing" valuePropName="checked" noStyle>
              <Switch />
              <span style={{ marginLeft: 8 }}>清除现有菜单（危险操作）</span>
            </Form.Item>
            
            <Form.Item name="import_permissions" valuePropName="checked" noStyle>
              <Switch />
              <span style={{ marginLeft: 8 }}>导入权限配置</span>
            </Form.Item>
          </Space>
        </Form.Item>

        <Alert
          message="导入说明"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>导入前建议先备份当前菜单配置</li>
              <li>"更新已存在的菜单"：如果菜单名称相同，则更新菜单信息</li>
              <li>"清除现有菜单"：导入前会删除所有现有菜单，请谨慎使用</li>
              <li>"导入权限配置"：同时导入菜单的权限和角色配置</li>
            </ul>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<UploadOutlined />}
              disabled={fileList.length === 0}
            >
              开始导入
            </Button>
            <Button onClick={handleCancel}>
              取消
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default MenuImport;