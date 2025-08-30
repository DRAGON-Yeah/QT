/**
 * 全局常量定义
 */

// API 基础配置
export const API_BASE_URL = '/api';
export const WS_BASE_URL = process.env.NODE_ENV === 'production' 
  ? `wss://${window.location.host}/ws`
  : `ws://${window.location.host}/ws`;

// 响应式断点配置
export const BREAKPOINTS = {
  xs: 0,      // 超小屏幕 <576px
  sm: 576,    // 小屏幕 ≥576px
  md: 768,    // 中等屏幕 ≥768px (平板端)
  lg: 992,    // 大屏幕 ≥992px
  xl: 1200,   // 超大屏幕 ≥1200px (桌面端)
  xxl: 1600,  // 超超大屏幕 ≥1600px
} as const;

// 主题配置
export const THEME_CONFIG = {
  // 主色调
  PRIMARY_COLOR: '#1890FF',
  
  // 功能色彩
  SUCCESS_COLOR: '#52C41A',
  WARNING_COLOR: '#FAAD14', 
  ERROR_COLOR: '#F5222D',
  INFO_COLOR: '#1890FF',
  
  // 交易专用色彩
  UP_COLOR: '#52C41A',      // 上涨绿色
  DOWN_COLOR: '#F5222D',    // 下跌红色
  NEUTRAL_COLOR: '#8C8C8C', // 平盘灰色
  
  // 风险等级色彩
  RISK_LOW: '#52C41A',      // 低风险
  RISK_MEDIUM: '#FAAD14',   // 中风险
  RISK_HIGH: '#F5222D',     // 高风险
  
  // 中性色
  TEXT_PRIMARY: '#262626',   // 主要文字
  TEXT_SECONDARY: '#8C8C8C', // 次要文字
  TEXT_DISABLED: '#BFBFBF',  // 禁用文字
  BACKGROUND: '#F5F5F5',     // 页面背景
  WHITE: '#FFFFFF',          // 纯白
  BLACK: '#000000',          // 纯黑
} as const;

// 字体规范
export const FONT_SIZES = {
  TITLE_LARGE: 24,    // 主标题
  TITLE_MEDIUM: 20,   // 次标题
  TITLE_SMALL: 16,    // 小标题
  TEXT_NORMAL: 14,    // 正文
  TEXT_SMALL: 12,     // 辅助文字
} as const;

// 间距规范
export const SPACING = {
  PAGE_PADDING: 24,     // 页面边距
  COMPONENT_GAP: 16,    // 组件间距
  ELEMENT_GAP: 8,       // 元素间距
  CONTENT_GAP: 4,       // 内容间距
} as const;

// 组件尺寸
export const COMPONENT_SIZES = {
  BUTTON_HEIGHT: 32,
  BUTTON_HEIGHT_LARGE: 48,
  BUTTON_HEIGHT_SMALL: 24,
  INPUT_HEIGHT: 32,
  CARD_BORDER_RADIUS: 6,
  SIDEBAR_WIDTH: 240,
  SIDEBAR_COLLAPSED_WIDTH: 64,
  HEADER_HEIGHT: 64,
} as const;

// 交易所配置
export const EXCHANGES = {
  BINANCE: {
    name: '币安',
    code: 'binance',
    icon: '/icons/binance.svg',
  },
  OKX: {
    name: '欧易',
    code: 'okx', 
    icon: '/icons/okx.svg',
  },
} as const;

// 订单类型
export const ORDER_TYPES = {
  MARKET: { label: '市价单', value: 'market' },
  LIMIT: { label: '限价单', value: 'limit' },
  STOP: { label: '止损单', value: 'stop' },
  STOP_LIMIT: { label: '止损限价单', value: 'stop_limit' },
} as const;

// 订单状态
export const ORDER_STATUS = {
  OPEN: { label: '待成交', value: 'open', color: '#1890FF' },
  PARTIAL: { label: '部分成交', value: 'partial', color: '#FAAD14' },
  FILLED: { label: '已成交', value: 'filled', color: '#52C41A' },
  CANCELLED: { label: '已取消', value: 'cancelled', color: '#8C8C8C' },
  REJECTED: { label: '已拒绝', value: 'rejected', color: '#F5222D' },
} as const;

// 时间周期
export const TIMEFRAMES = {
  '1m': '1分钟',
  '5m': '5分钟',
  '15m': '15分钟',
  '30m': '30分钟',
  '1h': '1小时',
  '4h': '4小时',
  '1d': '1天',
  '1w': '1周',
} as const;

// 技术指标
export const INDICATORS = {
  MA: { name: 'MA', label: '移动平均线' },
  EMA: { name: 'EMA', label: '指数移动平均线' },
  MACD: { name: 'MACD', label: 'MACD指标' },
  RSI: { name: 'RSI', label: 'RSI指标' },
  BOLL: { name: 'BOLL', label: '布林带' },
  KDJ: { name: 'KDJ', label: 'KDJ指标' },
} as const;

// 权限代码
export const PERMISSIONS = {
  // 用户管理
  USER_VIEW: 'users.view_user',
  USER_ADD: 'users.add_user',
  USER_CHANGE: 'users.change_user',
  USER_DELETE: 'users.delete_user',
  
  // 交易管理
  TRADING_VIEW: 'trading.view_order',
  TRADING_CREATE: 'trading.create_order',
  TRADING_CANCEL: 'trading.cancel_order',
  
  // 策略管理
  STRATEGY_VIEW: 'strategies.view_strategy',
  STRATEGY_CREATE: 'strategies.create_strategy',
  STRATEGY_EXECUTE: 'strategies.execute_strategy',
  
  // 系统管理
  SYSTEM_MONITOR: 'system.monitor',
  SYSTEM_CONFIG: 'system.config',
} as const;

/**
 * 路由路径常量 - 重新设计的菜单结构
 * 
 * 新的路由结构按功能模块进行分组，提供更清晰的导航层次：
 * - 基础路由：登录、仪表盘等核心页面
 * - 账户管理：用户、角色、交易所账户管理
 * - 交易中心：现货交易、订单管理、持仓管理等
 * - 策略管理：策略开发、回测、监控、风控
 * - 数据分析：市场分析、绩效分析、风险分析、报告
 * - 系统设置：菜单管理、系统监控、数据库管理等
 */
export const ROUTES = {
  // 基础路由 - 系统核心页面
  LOGIN: '/login',                    // 用户登录页面
  DASHBOARD: '/dashboard',            // 系统仪表盘
  
  // 账户管理模块 - 用户和权限相关功能
  ACCOUNT: '/account',                // 账户管理主页
  ACCOUNT_USERS: '/account/users',    // 用户管理页面
  ACCOUNT_ROLES: '/account/roles',    // 角色权限管理
  ACCOUNT_EXCHANGES: '/account/exchanges', // 交易所账户配置
  
  // 交易中心模块 - 交易相关功能
  TRADING: '/trading',                // 交易中心主页
  TRADING_SPOT: '/trading/spot',      // 现货交易界面
  TRADING_ORDERS: '/trading/orders',  // 订单管理页面
  TRADING_POSITIONS: '/trading/positions', // 持仓管理页面
  TRADING_HISTORY: '/trading/history', // 交易历史记录
  
  // 策略管理模块 - 量化策略相关功能
  STRATEGY: '/strategy',              // 策略管理主页
  STRATEGY_LIST: '/strategy/list',    // 策略列表页面
  STRATEGY_BACKTEST: '/strategy/backtest', // 策略回测页面
  STRATEGY_MONITOR: '/strategy/monitor',   // 策略监控页面
  STRATEGY_RISK: '/strategy/risk',    // 策略风险控制
  
  // 数据分析模块 - 数据分析和报告功能
  ANALYSIS: '/analysis',              // 数据分析主页
  ANALYSIS_MARKET: '/analysis/market', // 市场数据分析
  ANALYSIS_PERFORMANCE: '/analysis/performance', // 绩效分析页面
  ANALYSIS_RISK: '/analysis/risk',    // 风险分析页面
  ANALYSIS_REPORTS: '/analysis/reports', // 分析报告页面
  
  // 系统设置模块 - 系统管理和配置功能
  SYSTEM: '/system',                  // 系统设置主页
  SYSTEM_MENUS: '/system/menus',      // 菜单管理页面
  SYSTEM_MONITOR: '/system/monitor',  // 系统监控页面
  SYSTEM_DATABASE: '/system/database', // 数据库管理页面
  SYSTEM_LOGS: '/system/logs',        // 系统日志页面
  SYSTEM_CONFIG: '/system/config',    // 系统配置页面
  
  // 兼容旧路由（逐步废弃）- 为了向后兼容保留的旧路由映射
  USERS: '/account/users',            // 旧用户管理路由，重定向到新路由
  MENUS: '/system/menus',             // 旧菜单管理路由，重定向到新路由
  EXCHANGES: '/account/exchanges',    // 旧交易所管理路由，重定向到新路由
  STRATEGIES: '/strategy/list',       // 旧策略管理路由，重定向到新路由
  MARKET: '/analysis/market',         // 旧市场数据路由，重定向到新路由
  RISK: '/strategy/risk',             // 旧风险管理路由，重定向到新路由
  PROFILE: '/profile',                // 用户个人资料页面
} as const;

// 本地存储键名
export const STORAGE_KEYS = {
  TOKEN: 'quanttrade_token',
  USER: 'quanttrade_user',
  THEME: 'quanttrade_theme',
  LANGUAGE: 'quanttrade_language',
  SIDEBAR_COLLAPSED: 'quanttrade_sidebar_collapsed',
} as const;

// 分页配置
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  PAGE_SIZE_OPTIONS: ['10', '20', '50', '100'],
  SHOW_SIZE_CHANGER: true,
  SHOW_QUICK_JUMPER: true,
} as const;

// WebSocket事件类型
export const WS_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  TICKER_UPDATE: 'ticker_update',
  ORDER_UPDATE: 'order_update',
  POSITION_UPDATE: 'position_update',
  RISK_ALERT: 'risk_alert',
} as const;

// 图表配置
export const CHART_CONFIG = {
  COLORS: ['#1890FF', '#52C41A', '#FAAD14', '#F5222D', '#722ED1', '#13C2C2'],
  CANDLESTICK_UP: '#52C41A',
  CANDLESTICK_DOWN: '#F5222D',
  VOLUME_COLOR: 'rgba(24, 144, 255, 0.6)',
} as const;

// 表单验证规则
export const VALIDATION_RULES = {
  REQUIRED: { required: true, message: '此字段为必填项' },
  EMAIL: { 
    type: 'email' as const, 
    message: '请输入有效的邮箱地址' 
  },
  PASSWORD: {
    min: 8,
    message: '密码长度至少8位',
    pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
  },
  PHONE: {
    pattern: /^1[3-9]\d{9}$/,
    message: '请输入有效的手机号码',
  },
  PRICE: {
    pattern: /^\d+(\.\d{1,8})?$/,
    message: '请输入有效的价格',
  },
  AMOUNT: {
    pattern: /^\d+(\.\d{1,8})?$/,
    message: '请输入有效的数量',
  },
} as const;