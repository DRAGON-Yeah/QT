/**
 * 市场数据分析页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const MarketPage: React.FC = () => {
  return (
    <div className="market-page">
      <div className="page-header">
        <h1 className="page-title">市场数据</h1>
        <p className="page-description">实时市场数据和技术分析</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>市场数据分析页面</h3>
          <p>此页面将在任务 10.7 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default MarketPage;