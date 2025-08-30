/**
 * 仪表盘页面
 */

import React from 'react';
import { Row, Col } from 'antd';
import Card from '@/components/ui/Card';
import './style.scss';

const DashboardPage: React.FC = () => {
  return (
    <div className="dashboard-page">
      <div className="page-header">
        <h1 className="page-title">仪表盘</h1>
        <p className="page-description">量化交易系统概览</p>
      </div>
      
      <div className="dashboard-content">
        {/* 统计卡片 */}
        <Row gutter={[16, 16]} className="stats-row">
          <Col xs={24} sm={12} lg={6}>
            <Card.Stat
              title="总资产"
              value="¥125,680.50"
              prefix="¥"
              trend={{ value: 2.5, isPositive: true }}
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card.Stat
              title="今日盈亏"
              value="+¥1,250.30"
              trend={{ value: 1.2, isPositive: true }}
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card.Stat
              title="活跃策略"
              value="8"
              suffix="个"
            />
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card.Stat
              title="系统状态"
              value="正常"
            />
          </Col>
        </Row>
        
        {/* 图表区域 */}
        <Row gutter={[16, 16]} className="charts-row">
          <Col xs={24} lg={16}>
            <Card title="资产变化趋势" className="chart-card">
              <div className="chart-placeholder">
                <p>资产变化趋势图表</p>
                <p>（图表组件将在后续任务中实现）</p>
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={8}>
            <Card title="资产分布" className="chart-card">
              <div className="chart-placeholder">
                <p>资产分布饼图</p>
                <p>（图表组件将在后续任务中实现）</p>
              </div>
            </Card>
          </Col>
        </Row>
        
        {/* 快速操作区域 */}
        <Row gutter={[16, 16]} className="actions-row">
          <Col xs={24} md={12} lg={8}>
            <Card title="快速下单" hoverable className="action-card">
              <div className="action-content">
                <p>快速交易操作面板</p>
                <p>（将在交易页面任务中实现）</p>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={12} lg={8}>
            <Card title="策略管理" hoverable className="action-card">
              <div className="action-content">
                <p>策略快速管理</p>
                <p>（将在策略页面任务中实现）</p>
              </div>
            </Card>
          </Col>
          <Col xs={24} md={12} lg={8}>
            <Card title="风险监控" hoverable className="action-card">
              <div className="action-content">
                <p>实时风险监控</p>
                <p>（将在风险页面任务中实现）</p>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default DashboardPage;