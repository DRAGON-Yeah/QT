/**
 * 响应式Hook
 */

import { useState, useEffect } from 'react';
import { useAppStore } from '@/store';
import { BREAKPOINTS } from '@/constants';
import { getCurrentBreakpoint } from '@/utils';

interface ResponsiveInfo {
  /** 当前断点 */
  breakpoint: 'mobile' | 'tablet' | 'desktop';
  /** 是否为移动端 */
  isMobile: boolean;
  /** 是否为平板端 */
  isTablet: boolean;
  /** 是否为桌面端 */
  isDesktop: boolean;
  /** 屏幕宽度 */
  width: number;
  /** 屏幕高度 */
  height: number;
}

export const useResponsive = (): ResponsiveInfo => {
  const { setBreakpoint } = useAppStore();
  
  const [responsive, setResponsive] = useState<ResponsiveInfo>(() => {
    const breakpoint = getCurrentBreakpoint();
    return {
      breakpoint,
      isMobile: breakpoint === 'mobile',
      isTablet: breakpoint === 'tablet',
      isDesktop: breakpoint === 'desktop',
      width: window.innerWidth,
      height: window.innerHeight,
    };
  });

  useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      const breakpoint = getCurrentBreakpoint();
      
      const newResponsive: ResponsiveInfo = {
        breakpoint,
        isMobile: breakpoint === 'mobile',
        isTablet: breakpoint === 'tablet',
        isDesktop: breakpoint === 'desktop',
        width,
        height,
      };
      
      setResponsive(newResponsive);
      setBreakpoint(breakpoint);
    };

    // 添加事件监听器
    window.addEventListener('resize', handleResize);
    
    // 初始化时调用一次
    handleResize();

    // 清理事件监听器
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [setBreakpoint]);

  return responsive;
};

/**
 * 媒体查询Hook
 */
export const useMediaQuery = (query: string): boolean => {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia(query);
    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // 现代浏览器使用 addEventListener
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      // 兼容旧浏览器
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [query]);

  return matches;
};

/**
 * 断点Hook
 */
export const useBreakpoint = () => {
  const isMobile = useMediaQuery(`(max-width: ${BREAKPOINTS.md - 1}px)`);
  const isTablet = useMediaQuery(`(min-width: ${BREAKPOINTS.md}px) and (max-width: ${BREAKPOINTS.xl - 1}px)`);
  const isDesktop = useMediaQuery(`(min-width: ${BREAKPOINTS.xl}px)`);

  return {
    isMobile,
    isTablet,
    isDesktop,
    breakpoint: isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop',
  };
};