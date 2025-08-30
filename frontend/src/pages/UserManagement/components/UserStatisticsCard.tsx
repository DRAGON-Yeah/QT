/**
 * 用户统计卡片组件
 */
import React from 'react';
import { UserStatistics } from '../../../types';

interface UserStatisticsCardProps {
  statistics: UserStatistics;
}

const UserStatisticsCard: React.FC<UserStatisticsCardProps> = ({ statistics }) => {
  return (
    <div className="user-statistics">
      <div className="user-statistics__card user-statistics__card--primary">
        <div className="user-statistics__card-title">总用户数</div>
        <div className="user-statistics__card-value">{statistics.totalUsers}</div>
      </div>

      <div className="user-statistics__card user-statistics__card--success">
        <div className="user-statistics__card-title">活跃用户</div>
        <div className="user-statistics__card-value">{statistics.activeUsers}</div>
        <div className="user-statistics__card-change">
          占比 {statistics.totalUsers > 0 
            ? Math.round((statistics.activeUsers / statistics.totalUsers) * 100) 
            : 0}%
        </div>
      </div>

      <div className="user-statistics__card user-statistics__card--warning">
        <div className="user-statistics__card-title">管理员</div>
        <div className="user-statistics__card-value">{statistics.adminUsers}</div>
      </div>

      <div className="user-statistics__card user-statistics__card--danger">
        <div className="user-statistics__card-title">锁定用户</div>
        <div className="user-statistics__card-value">{statistics.lockedUsers}</div>
      </div>

      <div className="user-statistics__card">
        <div className="user-statistics__card-title">近7天登录</div>
        <div className="user-statistics__card-value">{statistics.recentLogins}</div>
        <div className="user-statistics__card-change">
          活跃度 {statistics.activeUsers > 0 
            ? Math.round((statistics.recentLogins / statistics.activeUsers) * 100) 
            : 0}%
        </div>
      </div>

      {/* 角色分布 */}
      <div className="user-statistics__card">
        <div className="user-statistics__card-title">角色分布</div>
        <div style={{ fontSize: '12px', marginTop: '8px' }}>
          {statistics.roleDistribution.map((role, index) => (
            <div key={index} style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              marginBottom: '4px'
            }}>
              <span>{role.name}</span>
              <span>{role.userCount}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserStatisticsCard;