/**
 * 全局类型定义
 */

// 用户相关类型
export interface User {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  avatar?: string;
  tenant: Tenant;
  tenantName?: string;
  roles: Role[];
  roleNames?: string[];
  permissions: string[];
  lastLogin?: string;
  lastLoginDisplay?: string;
  lastLoginIp?: string;
  lastActivity?: string;
  isActive: boolean;
  isTenantAdmin: boolean;
  passwordChangedAt?: string;
  failedLoginAttempts: number;
  lockedUntil?: string;
  language: string;
  timezoneName: string;
  dateJoined: string;
  profile?: UserProfile;
}

export interface Tenant {
  id: string;
  name: string;
  schemaName: string;
  domain?: string;
  isActive: boolean;
  maxUsers: number;
  maxStrategies: number;
  maxExchangeAccounts: number;
  subscriptionExpiresAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Role {
  id: number;
  name: string;
  description: string;
  roleType: 'system' | 'custom';
  isActive: boolean;
  permissions: Permission[];
  userCount?: number;
  createdAt: string;
  updatedAt: string;
}

export interface Permission {
  id: number;
  name: string;
  codename: string;
  category: 'system' | 'user' | 'trading' | 'strategy' | 'risk' | 'market' | 'monitoring';
  description: string;
}

// 交易所相关类型
export interface ExchangeAccount {
  id: number;
  name: string;
  exchange: 'binance' | 'okx';
  isActive: boolean;
  isTestnet: boolean;
  createdAt: string;
  assets?: Asset[];
}

export interface Asset {
  id: number;
  currency: string;
  total: number;
  available: number;
  locked: number;
  updatedAt: string;
}

// 交易相关类型
export interface Order {
  id: number;
  symbol: string;
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  side: 'buy' | 'sell';
  amount: number;
  price?: number;
  filled: number;
  remaining: number;
  status: 'open' | 'closed' | 'canceled' | 'expired' | 'rejected';
  createdAt: string;
  updatedAt: string;
}

export interface TradingPair {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  minOrderSize: number;
  maxOrderSize: number;
  pricePrecision: number;
  amountPrecision: number;
  isActive: boolean;
}

// 市场数据类型
export interface Ticker {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  volume: number;
  timestamp: string;
}

export interface Kline {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// 策略相关类型
export interface Strategy {
  id: number;
  name: string;
  description: string;
  code: string;
  parameters: Record<string, any>;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Backtest {
  id: number;
  strategy: Strategy;
  startDate: string;
  endDate: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  createdAt: string;
}

// 风险控制类型
export interface RiskMetrics {
  var: number;
  maxDrawdown: number;
  sharpeRatio: number;
  volatility: number;
  beta: number;
}

export interface RiskAlert {
  id: number;
  type: 'low' | 'medium' | 'high';
  message: string;
  createdAt: string;
  isRead: boolean;
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  code?: number;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next?: string;
  previous?: string;
}

// 主题相关类型
export interface ThemeConfig {
  primaryColor: string;
  mode: 'light' | 'dark';
  borderRadius: number;
  fontSize: number;
}

// 响应式断点类型
export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl';

// 组件通用属性
export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

// 表格列配置
export interface TableColumn<T = any> {
  key: string;
  title: string;
  dataIndex?: keyof T;
  render?: (value: any, record: T, index: number) => React.ReactNode;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
  sorter?: boolean | ((a: T, b: T) => number);
  filters?: Array<{ text: string; value: any }>;
  fixed?: 'left' | 'right';
}

// 用户配置类型
export interface UserProfile {
  realName?: string;
  idNumber?: string;
  birthDate?: string;
  address?: string;
  emergencyContact?: string;
  emergencyPhone?: string;
  defaultRiskLevel: 'low' | 'medium' | 'high';
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  theme: 'light' | 'dark' | 'auto';
  settings: Record<string, any>;
}

// 用户角色关联类型
export interface UserRole {
  id: number;
  role: number;
  roleName: string;
  roleDescription: string;
  assignedAt: string;
  assignedBy?: number;
  assignedByName?: string;
  expiresAt?: string;
  isActive: boolean;
}

// 登录日志类型
export interface LoginLog {
  id: number;
  username: string;
  userId?: string;
  ipAddress: string;
  userAgent: string;
  result: 'success' | 'failed' | 'blocked';
  failureReason?: string;
  attemptedAt: string;
}

// 用户统计类型
export interface UserStatistics {
  totalUsers: number;
  activeUsers: number;
  adminUsers: number;
  lockedUsers: number;
  recentLogins: number;
  roleDistribution: Array<{
    name: string;
    userCount: number;
  }>;
}

// 角色分配类型
export interface RoleAssignment {
  userIds: number[];
  roleIds: number[];
  action: 'add' | 'remove' | 'replace';
  expiresAt?: string;
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

// 表单验证规则
export interface ValidationRule {
  required?: boolean;
  message?: string;
  pattern?: RegExp;
  min?: number;
  max?: number;
  validator?: (value: any) => boolean | string;
}