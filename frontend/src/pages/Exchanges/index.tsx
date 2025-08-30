/**
 * 交易所账户管理页面
 * 
 * 功能：
 * - 交易所API密钥配置
 * - 账户余额查看
 * - 连接状态监控
 */

import React from 'react';
import { Card, Typography, Space, Alert } from 'antd';

const { Title, Paragraph } = Typography;

const ExchangesPage: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>交易所账户管理</Title>
          <Paragraph type="secondary">
            管理您的交易所API密钥，配置交易账户连接
          </Paragraph>
        </div>

        <Alert
          message="开发中"
          description="交易所账户管理功能正在开发中，敬请期待。"
          type="info"
          showIcon
        />

        <Card title="功能预览" style={{ width: '100%' }}>
          <Space direction="vertical" size="middle">
            <div>
              <Title level={4}>🔑 API密钥管理</Title>
              <Paragraph>
                安全地存储和管理您的交易所API密钥，支持币安、欧易等主流交易所。
              </Paragraph>
            </div>
            
            <div>
              <Title level={4}>💰 账户余额</Title>
              <Paragraph>
                实时查看各交易所账户余额，支持多币种资产统计。
              </Paragraph>
            </div>
            
            <div>
              <Title level={4}>📊 连接监控</Title>
              <Paragraph>
                监控交易所连接状态，确保API连接稳定可靠。
              </Paragraph>
            </div>
          </Space>
        </Card>
      </Space>
    </div>
  );
};

export default ExchangesPage;