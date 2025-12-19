/**
 * 常量定义
 */

// API配置
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  TIMEOUT: 30000,
};

// 应用配置
export const APP_CONFIG = {
  NAME: 'RootJourney',
  VERSION: '1.0.0',
};

// 时间格式
export const DATE_FORMAT = 'YYYY-MM-DD';
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss';

// 导出格式
export const EXPORT_FORMATS = {
  PDF: 'pdf',
  JSON: 'json',
  IMAGE: 'image',
};

