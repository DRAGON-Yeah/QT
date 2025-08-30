/**
 * 输入框组件
 */

import React from 'react';
import { Input as AntInput, InputProps as AntInputProps } from 'antd';
import classNames from 'classnames';
import './style.scss';

export interface InputProps extends AntInputProps {
  /** 输入框标签 */
  label?: string;
  /** 是否必填 */
  required?: boolean;
  /** 错误信息 */
  error?: string;
  /** 帮助信息 */
  help?: string;
  /** 自定义类名 */
  className?: string;
}

interface InputComponent extends React.FC<InputProps> {
  Password: React.FC<InputProps>;
  TextArea: React.FC<InputProps & { rows?: number }>;
  Search: React.FC<InputProps & { onSearch?: (value: string) => void }>;
}

const Input: InputComponent = ({
  label,
  required = false,
  error,
  help,
  className,
  ...props
}) => {
  const inputClass = classNames(
    'qt-input',
    {
      'qt-input--error': error,
    },
    className
  );

  const labelClass = classNames(
    'qt-input__label',
    {
      'qt-input__label--required': required,
    }
  );

  return (
    <div className="qt-input-wrapper">
      {label && (
        <label className={labelClass}>
          {label}
          {required && <span className="qt-input__required">*</span>}
        </label>
      )}
      <AntInput
        {...props}
        className={inputClass}
        status={error ? 'error' : undefined}
      />
      {error && <div className="qt-input__error">{error}</div>}
      {help && !error && <div className="qt-input__help">{help}</div>}
    </div>
  );
};

// 密码输入框
const Password: React.FC<InputProps> = (props) => {
  return <Input {...props} type="password" />;
};

// 文本域
const TextArea: React.FC<InputProps & { rows?: number }> = ({
  rows = 4,
  label,
  required = false,
  error,
  help,
  className,
  ...inputProps
}) => {
  
  const textareaClass = classNames(
    'qt-input',
    'qt-textarea',
    {
      'qt-input--error': error,
    },
    className
  );

  const labelClass = classNames(
    'qt-input__label',
    {
      'qt-input__label--required': required,
    }
  );

  return (
    <div className="qt-input-wrapper">
      {label && (
        <label className={labelClass}>
          {label}
          {required && <span className="qt-input__required">*</span>}
        </label>
      )}
      <AntInput.TextArea
        rows={rows}
        className={textareaClass}
        status={error ? 'error' : undefined}
        {...(inputProps as any)}
      />
      {error && <div className="qt-input__error">{error}</div>}
      {help && !error && <div className="qt-input__help">{help}</div>}
    </div>
  );
};

// 搜索框
const Search: React.FC<InputProps & { onSearch?: (value: string) => void }> = ({
  label,
  required = false,
  error,
  help,
  className,
  ...inputProps
}) => {
  
  const searchClass = classNames(
    'qt-input',
    'qt-search',
    {
      'qt-input--error': error,
    },
    className
  );

  return (
    <div className="qt-input-wrapper">
      {label && (
        <label className={classNames('qt-input__label', { 'qt-input__label--required': required })}>
          {label}
          {required && <span className="qt-input__required">*</span>}
        </label>
      )}
      <AntInput.Search
        className={searchClass}
        status={error ? 'error' : undefined}
        {...(inputProps as any)}
      />
      {error && <div className="qt-input__error">{error}</div>}
      {help && !error && <div className="qt-input__help">{help}</div>}
    </div>
  );
};

Input.Password = Password;
Input.TextArea = TextArea;
Input.Search = Search;

export default Input;