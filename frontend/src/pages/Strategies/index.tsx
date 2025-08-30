/**
 * 策略管理页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const StrategiesPage: React.FC = () => {
  return (
    <div className="strategies-page">
      <div className="page-header">
        <h1 className="page-title">策略管理</h1>
        <p className="page-description">开发、回测和管理交易策略</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>策略管理页面</h3>
          <p>此页面将在任务 10.5 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default StrategiesPage;