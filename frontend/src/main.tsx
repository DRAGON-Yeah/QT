/**
 * 应用入口文件
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// 导入请求拦截器
import './utils/request';

// 开发环境下导入测试工具
if (process.env.NODE_ENV === 'development') {
  // 导入路由测试工具
  import('./utils/routeTest');
  
  // 导入错误处理测试工具
  // import('./utils/errorHandlingTest');
}

// 创建根节点并渲染应用
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);