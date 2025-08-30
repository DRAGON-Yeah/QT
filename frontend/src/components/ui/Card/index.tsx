/**
 * 卡片组件
 */

import React from 'react';
import { Card as AntCard, CardProps as AntCardProps } from 'antd';
import classNames from 'classnames';
import './style.scss';

export interface CardProps extends AntCardProps {
  /** 卡片标题 */
  title?: React.ReactNode;
  /** 卡片额外操作 */
  extra?: React.ReactNode;
  /** 是否显示边框 */
  bordered?: boolean;
  /** 是否可悬停 */
  hoverable?: boolean;
  /** 加载状态 */
  loading?: boolean;
  /** 卡片尺寸 */
  size?: 'default' | 'small';
  /** 自定义类名 */
  className?: string;
  /** 子元素 */
  children?: React.ReactNode;
}

interface CardComponent extends React.FC<CardProps> {
  Stat: React.FC<StatCardProps>;
}

const Card: CardComponent = ({
  title,
  extra,
  bordered = true,
  hoverable = false,
  loading = false,
  size = 'default',
  className,
  children,
  ...props
}) => {
  const cardClass = classNames(
    'qt-card',
    `qt-card--${size}`,
    {
      'qt-card--hoverable': hoverable,
      'qt-card--loading': loading,
    },
    className
  );

  return (
    <AntCard
      {...props}
      title={title}
      extra={extra}
      bordered={bordered}
      hoverable={hoverable}
      loading={loading}
      size={size}
      className={cardClass}
    >
      {children}
    </AntCard>
  );
};

// 统计卡片
interface StatCardProps {
  title: string;
  value: string | number;
  prefix?: React.ReactNode;
  suffix?: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  prefix,
  suffix,
  trend,
  loading = false,
  className,
}) => {
  const statClass = classNames('qt-stat-card', className);

  return (
    <Card className={statClass} loading={loading} hoverable>
      <div className="qt-stat-card__content">
        <div className="qt-stat-card__title">{title}</div>
        <div className="qt-stat-card__value">
          {prefix && <span className="qt-stat-card__prefix">{prefix}</span>}
          <span className="qt-stat-card__number">{value}</span>
          {suffix && <span className="qt-stat-card__suffix">{suffix}</span>}
        </div>
        {trend && (
          <div className={`qt-stat-card__trend ${trend.isPositive ? 'positive' : 'negative'}`}>
            <span className="qt-stat-card__trend-icon">
              {trend.isPositive ? '↗' : '↘'}
            </span>
            <span className="qt-stat-card__trend-value">
              {Math.abs(trend.value)}%
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

Card.Stat = StatCard;

export default Card;