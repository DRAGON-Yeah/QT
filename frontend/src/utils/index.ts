/**
 * 工具函数库
 */

import dayjs from 'dayjs';
import { THEME_CONFIG } from '@/constants';

/**
 * 格式化数字
 */
export const formatNumber = (
  value: number | string,
  options: {
    decimals?: number;
    thousandsSeparator?: boolean;
    prefix?: string;
    suffix?: string;
  } = {}
): string => {
  const {
    decimals = 2,
    thousandsSeparator = true,
    prefix = '',
    suffix = '',
  } = options;

  const num = typeof value === 'string' ? parseFloat(value) : value;
  
  if (isNaN(num)) return '--';

  let formatted = num.toFixed(decimals);
  
  if (thousandsSeparator) {
    formatted = formatted.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  return `${prefix}${formatted}${suffix}`;
};

/**
 * 格式化价格
 */
export const formatPrice = (price: number | string, precision = 2): string => {
  return formatNumber(price, { decimals: precision, thousandsSeparator: true });
};

/**
 * 格式化百分比
 */
export const formatPercent = (value: number | string, decimals = 2): string => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '--';
  
  return formatNumber(num * 100, { decimals, suffix: '%' });
};

/**
 * 格式化涨跌幅
 */
export const formatChange = (change: number | string): {
  value: string;
  color: string;
  prefix: string;
} => {
  const num = typeof change === 'string' ? parseFloat(change) : change;
  
  if (isNaN(num)) {
    return { value: '--', color: THEME_CONFIG.NEUTRAL_COLOR, prefix: '' };
  }

  const color = num > 0 
    ? THEME_CONFIG.UP_COLOR 
    : num < 0 
    ? THEME_CONFIG.DOWN_COLOR 
    : THEME_CONFIG.NEUTRAL_COLOR;
    
  const prefix = num > 0 ? '+' : '';
  const value = formatPercent(num);

  return { value, color, prefix };
};

/**
 * 格式化时间
 */
export const formatTime = (
  time: string | number | Date,
  format = 'YYYY-MM-DD HH:mm:ss'
): string => {
  return dayjs(time).format(format);
};

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (time: string | number | Date): string => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss');
};

/**
 * 获取涨跌颜色
 */
export const getChangeColor = (value: number): string => {
  if (value > 0) return THEME_CONFIG.UP_COLOR;
  if (value < 0) return THEME_CONFIG.DOWN_COLOR;
  return THEME_CONFIG.NEUTRAL_COLOR;
};

/**
 * 获取风险等级颜色
 */
export const getRiskColor = (level: 'low' | 'medium' | 'high'): string => {
  switch (level) {
    case 'low':
      return THEME_CONFIG.RISK_LOW;
    case 'medium':
      return THEME_CONFIG.RISK_MEDIUM;
    case 'high':
      return THEME_CONFIG.RISK_HIGH;
    default:
      return THEME_CONFIG.NEUTRAL_COLOR;
  }
};

/**
 * 防抖函数
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * 节流函数
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * 深拷贝
 */
export const deepClone = <T>(obj: T): T => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime()) as any;
  if (obj instanceof Array) return obj.map(item => deepClone(item)) as any;
  if (typeof obj === 'object') {
    const clonedObj = {} as any;
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        clonedObj[key] = deepClone(obj[key]);
      }
    }
    return clonedObj;
  }
  return obj;
};

/**
 * 生成唯一ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

/**
 * 检查是否为移动设备
 */
export const isMobile = (): boolean => {
  return window.innerWidth < 768;
};

/**
 * 检查是否为平板设备
 */
export const isTablet = (): boolean => {
  return window.innerWidth >= 768 && window.innerWidth < 1200;
};

/**
 * 检查是否为桌面设备
 */
export const isDesktop = (): boolean => {
  return window.innerWidth >= 1200;
};

/**
 * 获取当前断点
 */
export const getCurrentBreakpoint = (): 'mobile' | 'tablet' | 'desktop' => {
  if (isMobile()) return 'mobile';
  if (isTablet()) return 'tablet';
  return 'desktop';
};

/**
 * 本地存储工具
 */
export const storage = {
  get: <T>(key: string, defaultValue?: T): T | null => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue || null;
    } catch {
      return defaultValue || null;
    }
  },
  
  set: (key: string, value: any): void => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Failed to save to localStorage:', error);
    }
  },
  
  remove: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Failed to remove from localStorage:', error);
    }
  },
  
  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      console.error('Failed to clear localStorage:', error);
    }
  },
};

/**
 * URL参数工具
 */
export const urlParams = {
  get: (key: string): string | null => {
    const params = new URLSearchParams(window.location.search);
    return params.get(key);
  },
  
  set: (key: string, value: string): void => {
    const url = new URL(window.location.href);
    url.searchParams.set(key, value);
    window.history.replaceState({}, '', url.toString());
  },
  
  remove: (key: string): void => {
    const url = new URL(window.location.href);
    url.searchParams.delete(key);
    window.history.replaceState({}, '', url.toString());
  },
};

/**
 * 文件下载
 */
export const downloadFile = (data: Blob | string, filename: string): void => {
  const blob = typeof data === 'string' ? new Blob([data]) : data;
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
};

/**
 * 复制到剪贴板
 */
export const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      return true;
    } else {
      // 降级方案
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    }
  } catch {
    return false;
  }
};

/**
 * 验证交易对格式
 */
export const validateSymbol = (symbol: string): boolean => {
  return /^[A-Z]{2,10}\/[A-Z]{2,10}$/.test(symbol);
};

/**
 * 验证价格格式
 */
export const validatePrice = (price: string | number): boolean => {
  const num = typeof price === 'string' ? parseFloat(price) : price;
  return !isNaN(num) && num > 0;
};

/**
 * 计算精度
 */
export const getPrecision = (value: number): number => {
  const str = value.toString();
  const decimal = str.split('.')[1];
  return decimal ? decimal.length : 0;
};

/**
 * 安全的JSON解析
 */
export const safeJsonParse = <T>(str: string, defaultValue: T): T => {
  try {
    return JSON.parse(str);
  } catch {
    return defaultValue;
  }
};