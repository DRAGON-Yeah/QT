import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

/**
 * Vite 配置文件
 * 
 * 为 QuantTrade 前端项目配置开发服务器、构建选项、路径别名等
 * 支持 React + TypeScript 开发环境
 * 
 * @see https://vitejs.dev/config/
 */
export default defineConfig({
  // 插件配置
  plugins: [
    react(), // React 支持插件，提供 JSX 转换和热重载
  ],
  
  // 开发服务器配置
  server: {
    host: '0.0.0.0', // 监听所有网络接口，允许外部访问（Docker 容器需要）
    port: 3000,      // 开发服务器端口
    strictPort: false, // 端口被占用时自动尝试下一个可用端口
    
    // 代理配置 - 开发环境下将 API 请求代理到后端服务
    proxy: {
      // API 请求代理到 Django 后端
      '/api': {
        target: 'http://backend:8000',  // Docker 容器内的后端服务地址
        changeOrigin: true,             // 修改请求头中的 origin 字段
        secure: false,                  // 不验证 SSL 证书（开发环境）
      },
      // Django 管理后台代理
      '/admin': {
        target: 'http://backend:8000',
        changeOrigin: true,
        secure: false,
      },
      // WebSocket 连接代理（用于实时数据推送）
      '/ws': {
        target: 'ws://backend:8000',    // WebSocket 协议
        ws: true,                       // 启用 WebSocket 代理
        changeOrigin: true,
      },
    },
  },
  
  // 生产环境构建配置
  build: {
    outDir: 'dist',      // 构建输出目录
    sourcemap: false,    // 生产环境不生成 sourcemap（减小包体积）
    
    // Rollup 打包配置
    rollupOptions: {
      output: {
        // 手动分包策略 - 优化加载性能
        manualChunks: {
          // 基础框架包 - React 相关
          vendor: ['react', 'react-dom'],
          // UI 组件库包 - Ant Design 相关
          antd: ['antd', '@ant-design/icons'],
          // 图表库包 - ECharts 相关
          charts: ['echarts', 'echarts-for-react'],
        },
      },
    },
  },
  
  // 模块解析配置
  resolve: {
    // 路径别名配置 - 简化导入路径
    alias: {
      '@': path.resolve(__dirname, './src'),                    // 根目录别名
      '@components': path.resolve(__dirname, './src/components'), // 组件目录
      '@pages': path.resolve(__dirname, './src/pages'),         // 页面目录
      '@utils': path.resolve(__dirname, './src/utils'),         // 工具函数目录
      '@services': path.resolve(__dirname, './src/services'),   // API 服务目录
      '@types': path.resolve(__dirname, './src/types'),         // TypeScript 类型定义目录
      '@assets': path.resolve(__dirname, './src/assets'),       // 静态资源目录
    },
  },
  
  // 环境变量配置
  envPrefix: 'REACT_APP_', // 只有以 REACT_APP_ 开头的环境变量会被暴露给客户端
  
  // CSS 预处理器配置
  css: {
    preprocessorOptions: {
      scss: {
        // 自动导入全局 SCSS 变量文件（使用现代 @use 语法替代已弃用的 @import）
        // @use 语法优势：模块化导入、避免重复编译、更好的命名空间管理
        additionalData: `@use "@/styles/variables.scss" as *;`,
        
        // 使用现代 Sass 编译器 API（替代传统的 legacy API）
        // 现代 API 优势：更快的编译速度、更好的错误报告、更高效的内存使用
        api: 'modern-compiler',
      },
    },
  },
})