/**
 * 输入框组件测试
 */

// import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import Input from '../index';

describe('Input Component', () => {
  it('renders correctly', () => {
    render(<Input placeholder="请输入内容" />);
    expect(screen.getByPlaceholderText('请输入内容')).toBeInTheDocument();
  });

  it('renders with label', () => {
    render(<Input label="用户名" />);
    expect(screen.getByText('用户名')).toBeInTheDocument();
  });

  it('shows required indicator', () => {
    render(<Input label="密码" required />);
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(<Input error="输入错误" />);
    expect(screen.getByText('输入错误')).toBeInTheDocument();
  });

  it('displays help text', () => {
    render(<Input help="帮助信息" />);
    expect(screen.getByText('帮助信息')).toBeInTheDocument();
  });

  it('handles value changes', () => {
    const handleChange = vi.fn();
    render(<Input onChange={handleChange} />);
    
    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: '测试内容' } });
    
    expect(handleChange).toHaveBeenCalled();
  });
});