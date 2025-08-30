/**
 * 工具函数测试
 */

import { describe, it, expect } from 'vitest';
import {
  formatNumber,
  formatPrice,
  formatPercent,
  formatChange,
  validateSymbol,
  validatePrice,
  getPrecision,
} from '../index';

describe('Utils Functions', () => {
  describe('formatNumber', () => {
    it('formats numbers correctly', () => {
      expect(formatNumber(1234.56)).toBe('1,234.56');
      expect(formatNumber(1234.56, { decimals: 0 })).toBe('1,235');
      expect(formatNumber(1234.56, { prefix: '$' })).toBe('$1,234.56');
      expect(formatNumber(1234.56, { suffix: '%' })).toBe('1,234.56%');
    });

    it('handles invalid input', () => {
      expect(formatNumber('invalid')).toBe('--');
      expect(formatNumber(NaN)).toBe('--');
    });
  });

  describe('formatPrice', () => {
    it('formats prices correctly', () => {
      expect(formatPrice(45000.123)).toBe('45,000.12');
      expect(formatPrice(45000.123, 4)).toBe('45,000.1230');
    });
  });

  describe('formatPercent', () => {
    it('formats percentages correctly', () => {
      expect(formatPercent(0.1234)).toBe('12.34%');
      expect(formatPercent(0.1234, 1)).toBe('12.3%');
    });
  });

  describe('formatChange', () => {
    it('formats positive changes correctly', () => {
      const result = formatChange(0.05);
      expect(result.value).toBe('5.00%');
      expect(result.prefix).toBe('+');
    });

    it('formats negative changes correctly', () => {
      const result = formatChange(-0.03);
      expect(result.value).toBe('-3.00%');
      expect(result.prefix).toBe('');
    });

    it('handles zero change', () => {
      const result = formatChange(0);
      expect(result.value).toBe('0.00%');
      expect(result.prefix).toBe('');
    });
  });

  describe('validateSymbol', () => {
    it('validates trading symbols correctly', () => {
      expect(validateSymbol('BTC/USDT')).toBe(true);
      expect(validateSymbol('ETH/BTC')).toBe(true);
      expect(validateSymbol('BTCUSDT')).toBe(false);
      expect(validateSymbol('BTC-USDT')).toBe(false);
      expect(validateSymbol('btc/usdt')).toBe(false);
    });
  });

  describe('validatePrice', () => {
    it('validates prices correctly', () => {
      expect(validatePrice(100)).toBe(true);
      expect(validatePrice('100.50')).toBe(true);
      expect(validatePrice(0)).toBe(false);
      expect(validatePrice(-100)).toBe(false);
      expect(validatePrice('invalid')).toBe(false);
    });
  });

  describe('getPrecision', () => {
    it('calculates precision correctly', () => {
      expect(getPrecision(123.45)).toBe(2);
      expect(getPrecision(123)).toBe(0);
      expect(getPrecision(123.456789)).toBe(6);
    });
  });
});