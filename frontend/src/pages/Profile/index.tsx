/**
 * 个人中心页面
 */

import React from 'react';
import Card from '@/components/ui/Card';

const ProfilePage: React.FC = () => {
  return (
    <div className="profile-page">
      <div className="page-header">
        <h1 className="page-title">个人中心</h1>
        <p className="page-description">个人信息和账户设置</p>
      </div>
      
      <Card>
        <div style={{ textAlign: 'center', padding: '60px 20px', color: '#999' }}>
          <h3>个人中心页面</h3>
          <p>此页面将在任务 10.3 中实现</p>
        </div>
      </Card>
    </div>
  );
};

export default ProfilePage;