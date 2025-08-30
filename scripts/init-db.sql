-- QuantTrade 数据库初始化脚本

-- 创建数据库（如果不存在）
-- CREATE DATABASE IF NOT EXISTS quanttrade_dev;

-- 设置字符集
-- ALTER DATABASE quanttrade_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- PostgreSQL 初始化
-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建索引类型
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS 会在实际使用时创建

-- 初始化完成
SELECT 'QuantTrade 数据库初始化完成' as message;