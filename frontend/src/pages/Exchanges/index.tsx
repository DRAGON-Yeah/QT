/**
 * 交易所管理页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const ExchangesPage: React.FC = () => {
  return (
    <div className="exchanges-page">
      <div className="page-header">
        <h1 className="page-title">交易所管理</h1>
        <p className="page-description">管理交易所账户和API配置</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>交易所管理页面</h3>
          <p>此页面将在任务 10.4 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default ExchangesPage;