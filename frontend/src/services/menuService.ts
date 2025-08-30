import axios from 'axios';

const API_BASE_URL = '/api/core';

export interface MenuNode {
  id: number;
  name: string;
  title: string;
  icon: string;
  path: string;
  component: string;
  menu_type: string;
  target: string;
  level: number;
  sort_order: number;
  is_visible: boolean;
  is_enabled: boolean;
  parent_id?: number;
  children?: MenuNode[];
  permissions?: number[];
  roles?: number[];
  meta?: any;
}

export interface MenuFormData {
  name: string;
  title: string;
  icon?: string;
  path?: string;
  component?: string;
  parent_id?: number;
  menu_type: string;
  target: string;
  sort_order: number;
  permissions?: number[];
  roles?: number[];
  is_visible: boolean;
  is_enabled: boolean;
  is_cache: boolean;
  meta_info?: any;
}

export interface UserMenuConfig {
  id: number;
  menu: number;
  is_favorite: boolean;
  is_hidden: boolean;
  custom_title?: string;
  custom_icon?: string;
  custom_sort: number;
  access_count: number;
  last_access_time?: string;
}

class MenuService {
  // 获取菜单树
  async getMenuTree() {
    return axios.get(`${API_BASE_URL}/menus/tree/`);
  }

  // 获取菜单列表
  async getMenus(params?: any) {
    return axios.get(`${API_BASE_URL}/menus/`, { params });
  }

  // 获取单个菜单
  async getMenu(id: number) {
    return axios.get(`${API_BASE_URL}/menus/${id}/`);
  }

  // 创建菜单
  async createMenu(data: MenuFormData) {
    return axios.post(`${API_BASE_URL}/menus/`, data);
  }

  // 更新菜单
  async updateMenu(id: number, data: Partial<MenuFormData>) {
    return axios.put(`${API_BASE_URL}/menus/${id}/`, data);
  }

  // 删除菜单
  async deleteMenu(id: number) {
    return axios.delete(`${API_BASE_URL}/menus/${id}/`);
  }

  // 重新排序菜单
  async reorderMenus(menus: Array<{ id: number; sort_order: number; parent_id?: number }>) {
    return axios.post(`${API_BASE_URL}/menus/reorder/`, { menus });
  }

  // 切换菜单可见性
  async toggleVisibility(id: number) {
    return axios.post(`${API_BASE_URL}/menus/${id}/toggle_visibility/`);
  }

  // 切换菜单启用状态
  async toggleEnabled(id: number) {
    return axios.post(`${API_BASE_URL}/menus/${id}/toggle_enabled/`);
  }

  // 获取权限列表
  async getPermissions() {
    return axios.get(`${API_BASE_URL}/menus/permissions/`);
  }

  // 获取角色列表
  async getRoles() {
    return axios.get(`${API_BASE_URL}/menus/roles/`);
  }

  // 获取图标列表
  async getIcons() {
    return axios.get(`${API_BASE_URL}/menus/icons/`);
  }

  // 获取菜单统计
  async getMenuStats() {
    return axios.get(`${API_BASE_URL}/menus/stats/`);
  }

  // 用户菜单配置相关
  
  // 获取用户菜单配置
  async getUserMenuConfigs() {
    return axios.get(`${API_BASE_URL}/user-menu-configs/`);
  }

  // 获取收藏菜单
  async getFavoriteMenus() {
    return axios.get(`${API_BASE_URL}/user-menu-configs/favorites/`);
  }

  // 切换菜单收藏状态
  async toggleFavorite(configId: number) {
    return axios.post(`${API_BASE_URL}/user-menu-configs/${configId}/toggle_favorite/`);
  }

  // 记录菜单访问
  async recordMenuAccess(menuId: number) {
    return axios.post(`${API_BASE_URL}/user-menu-configs/${menuId}/access/`);
  }

  // 批量配置菜单
  async batchConfigMenus(configs: Array<{
    menu_id: number;
    is_favorite?: boolean;
    is_hidden?: boolean;
    custom_title?: string;
    custom_icon?: string;
    custom_sort?: number;
  }>) {
    return axios.post(`${API_BASE_URL}/user-menu-configs/batch_config/`, { configs });
  }

  // 创建用户菜单配置
  async createUserMenuConfig(data: Partial<UserMenuConfig>) {
    return axios.post(`${API_BASE_URL}/user-menu-configs/`, data);
  }

  // 更新用户菜单配置
  async updateUserMenuConfig(id: number, data: Partial<UserMenuConfig>) {
    return axios.put(`${API_BASE_URL}/user-menu-configs/${id}/`, data);
  }

  // 删除用户菜单配置
  async deleteUserMenuConfig(id: number) {
    return axios.delete(`${API_BASE_URL}/user-menu-configs/${id}/`);
  }

  // 导出菜单配置
  async exportMenus() {
    return axios.get(`${API_BASE_URL}/menus/export/`, {
      responseType: 'blob'
    });
  }

  // 导入菜单配置
  async importMenus(file: File, options?: {
    clear_existing?: boolean;
    update_existing?: boolean;
    import_permissions?: boolean;
  }) {
    const formData = new FormData();
    formData.append('file', file);
    
    if (options) {
      Object.entries(options).forEach(([key, value]) => {
        formData.append(key, value.toString());
      });
    }
    
    return axios.post(`${API_BASE_URL}/menus/import_menus/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }

  // 预热缓存
  async warmCache() {
    return axios.post(`${API_BASE_URL}/menus/warm_cache/`);
  }

  // 获取性能统计
  async getPerformanceStats() {
    return axios.get(`${API_BASE_URL}/menus/performance/`);
  }
}

export const menuService = new MenuService();