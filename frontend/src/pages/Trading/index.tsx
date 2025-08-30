/**
 * 交易执行页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const TradingPage: React.FC = () => {
  return (
    <div className="trading-page">
      <div className="page-header">
        <h1 className="page-title">交易执行</h1>
        <p className="page-description">执行交易订单和管理持仓</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>交易执行页面</h3>
          <p>此页面将在任务 10.6 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default TradingPage;