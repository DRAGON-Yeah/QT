/**
 * 系统管理页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const SystemPage: React.FC = () => {
  return (
    <div className="system-page">
      <div className="page-header">
        <h1 className="page-title">系统管理</h1>
        <p className="page-description">用户管理、权限配置和系统监控</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>系统管理页面</h3>
          <p>此页面将在任务 10.8 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default SystemPage;