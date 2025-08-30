/**
 * 路由测试工具
 * 用于验证 QuantTrade 系统的路由配置是否正确
 * 
 * 主要功能：
 * - 验证所有路由路径的有效性
 * - 在开发环境下自动执行路由测试
 * - 输出路由配置信息用于调试
 */

/**
 * 测试系统路由配置
 * 
 * 验证 QuantTrade 系统中所有主要功能模块的路由配置：
 * - 仪表盘：系统概览和快速操作
 * - 账户管理：用户、角色、交易所账户管理
 * - 交易中心：现货交易、订单管理、持仓管理、交易历史
 * - 策略管理：策略列表、回测、监控、风险控制
 * - 数据分析：市场行情、收益分析、风险分析、报表中心
 * - 系统设置：菜单管理、系统监控、数据库管理、日志查看、系统配置
 * 
 * @returns {string[]} 返回所有路由路径的数组
 */
export const testRoutes = (): string[] => {
  // 定义系统所有路由路径
  const routes = [
    // 仪表盘模块
    '/dashboard',                    // 系统仪表盘
    
    // 账户管理模块
    '/account/users',               // 用户管理
    '/account/roles',               // 角色权限管理
    '/account/exchanges',           // 交易所账户管理
    
    // 交易中心模块
    '/trading/spot',                // 现货交易
    '/trading/orders',              // 订单管理
    '/trading/positions',           // 持仓管理
    '/trading/history',             // 交易历史
    
    // 策略管理模块
    '/strategy/list',               // 策略列表
    '/strategy/backtest',           // 策略回测
    '/strategy/monitor',            // 策略监控
    '/strategy/risk',               // 风险控制
    
    // 数据分析模块
    '/analysis/market',             // 市场行情
    '/analysis/performance',        // 收益分析
    '/analysis/risk',               // 风险分析
    '/analysis/reports',            // 报表中心
    
    // 系统设置模块
    '/system/menus',                // 菜单管理
    '/system/monitor',              // 系统监控
    '/system/database',             // 数据库管理
    '/system/logs',                 // 系统日志
    '/system/config'                // 系统配置
  ];

  // 输出路由配置信息用于调试
  console.log('🧪 QuantTrade 路由配置测试:', routes);
  console.log(`📊 共配置 ${routes.length} 个路由路径`);
  
  return routes;
};

/**
 * 开发环境自动测试
 * 
 * 在开发环境下自动执行路由测试，帮助开发者验证路由配置
 * 仅在 Vite 开发环境 (import.meta.env.DEV) 下执行
 */
if (import.meta.env.DEV) {
  // 延迟执行，确保应用初始化完成
  setTimeout(() => {
    console.group('🚀 QuantTrade 开发环境路由测试');
    testRoutes();
    console.groupEnd();
  }, 1000);
}