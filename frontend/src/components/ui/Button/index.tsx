/**
 * 按钮组件
 */

import React from 'react';
import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';
import classNames from 'classnames';
import './style.scss';

export interface ButtonProps extends Omit<AntButtonProps, 'size' | 'type' | 'variant'> {
  /** 按钮尺寸 */
  size?: 'small' | 'middle' | 'large';
  /** 按钮变体 */
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'ghost' | 'text';
  /** 是否为块级按钮 */
  block?: boolean;
  /** 自定义类名 */
  className?: string;
  /** 子元素 */
  children?: React.ReactNode;
}

const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'middle',
  loading = false,
  disabled = false,
  block = false,
  className,
  children,
  ...props
}) => {
  const buttonClass = classNames(
    'qt-button',
    `qt-button--${variant}`,
    `qt-button--${size}`,
    {
      'qt-button--block': block,
      'qt-button--loading': loading,
      'qt-button--disabled': disabled,
    },
    className
  );

  // 根据变体设置 Ant Design 的 type
  const getAntType = (): AntButtonProps['type'] => {
    switch (variant) {
      case 'primary':
        return 'primary';
      case 'success':
      case 'warning':
      case 'danger':
        return 'primary';
      case 'ghost':
        return 'default';
      case 'text':
        return 'text';
      default:
        return 'default';
    }
  };

  return (
    <AntButton
      {...props}
      type={getAntType()}
      size={size}
      loading={loading}
      disabled={disabled}
      block={block}
      className={buttonClass}
      icon={loading ? <LoadingOutlined /> : props.icon}
    >
      {children}
    </AntButton>
  );
};

export default Button;