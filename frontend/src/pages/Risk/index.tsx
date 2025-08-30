/**
 * 风险控制页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const RiskPage: React.FC = () => {
  return (
    <div className="risk-page">
      <div className="page-header">
        <h1 className="page-title">风险控制</h1>
        <p className="page-description">实时风险监控和预警管理</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>风险控制页面</h3>
          <p>此页面将在任务 10.8 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default RiskPage;