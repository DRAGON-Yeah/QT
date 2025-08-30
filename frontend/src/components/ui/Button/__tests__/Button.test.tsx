/**
 * 按钮组件测试
 */

// import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Button from '../index';

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>测试按钮</Button>);
    expect(screen.getByText('测试按钮')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>点击按钮</Button>);
    
    fireEvent.click(screen.getByText('点击按钮'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies variant classes correctly', () => {
    const { container } = render(<Button variant="success">成功按钮</Button>);
    expect(container.firstChild).toHaveClass('qt-button--success');
  });

  it('shows loading state', () => {
    render(<Button loading>加载中</Button>);
    expect(screen.getByText('加载中')).toBeInTheDocument();
  });

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>禁用按钮</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});