/**
 * API调用服务 (Axios封装)
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // TODO: 添加认证token
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API错误:', error);
    return Promise.reject(error);
  }
);

// 用户相关API
export const createUser = (userData) => {
  return api.post('/api/users/', userData);
};

export const getUser = (userId) => {
  return api.get(`/api/users/${userId}`);
};

// AI聊天API
export const sendMessage = (messages, context = {}) => {
  return api.post('/api/chat/', { messages, context });
};

// 搜索API
export const search = (query, filters = {}) => {
  return api.post('/api/search/', { query, filters });
};

// 生成API
export const generateReport = (userId) => {
  return api.post(`/api/generate/report?user_id=${userId}`);
};

export const generateBiography = (personId) => {
  return api.post(`/api/generate/biography/${personId}`);
};

export const generateTimeline = (personId) => {
  return api.post(`/api/generate/timeline/${personId}`);
};

// 导出API
export const exportPDF = (reportId) => {
  return api.get(`/api/export/pdf/${reportId}`, { responseType: 'blob' });
};

export const exportJSON = (reportId) => {
  return api.get(`/api/export/json/${reportId}`);
};

export const exportFamilyTreeImage = (familyTreeId) => {
  return api.get(`/api/export/image/${familyTreeId}`, { responseType: 'blob' });
};

export default api;

