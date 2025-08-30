import { noAutoLogoutFetch } from '../utils/request';

// API基础路径
const API_BASE_URL = '/api/core';

/**
 * 菜单节点接口定义
 * 用于描述菜单树结构中的单个节点
 */
export interface MenuNode {
  id: number;                    // 菜单ID
  name: string;                  // 菜单名称（英文标识）
  title: string;                 // 菜单标题（显示名称）
  icon: string;                  // 菜单图标
  path: string;                  // 路由路径
  component: string;             // 组件路径
  menu_type: string;             // 菜单类型：menu/button/link
  target: string;                // 打开方式：_self/_blank
  level: number;                 // 菜单层级
  sort_order: number;            // 排序顺序
  is_visible: boolean;           // 是否可见
  is_enabled: boolean;           // 是否启用
  parent_id?: number;            // 父菜单ID
  children?: MenuNode[];         // 子菜单列表
  permissions?: number[];        // 所需权限ID列表
  roles?: number[];              // 可访问角色ID列表
  meta?: any;                    // 元信息
}

/**
 * 菜单表单数据接口
 * 用于创建和更新菜单时的数据结构
 */
export interface MenuFormData {
  name: string;                  // 菜单名称（英文标识）
  title: string;                 // 菜单标题（显示名称）
  icon?: string;                 // 菜单图标（可选）
  path?: string;                 // 路由路径（可选）
  component?: string;            // 组件路径（可选）
  parent_id?: number;            // 父菜单ID（可选）
  menu_type: string;             // 菜单类型：menu/button/link
  target: string;                // 打开方式：_self/_blank
  sort_order: number;            // 排序顺序
  permissions?: number[];        // 所需权限ID列表（可选）
  roles?: number[];              // 可访问角色ID列表（可选）
  is_visible: boolean;           // 是否可见
  is_enabled: boolean;           // 是否启用
  is_cache: boolean;             // 是否缓存
  meta_info?: any;               // 元信息（可选）
}

/**
 * 用户菜单配置接口
 * 用于描述用户对菜单的个性化配置
 */
export interface UserMenuConfig {
  id: number;                    // 配置ID
  menu: number;                  // 菜单ID
  is_favorite: boolean;          // 是否收藏
  is_hidden: boolean;            // 是否隐藏
  custom_title?: string;         // 自定义标题（可选）
  custom_icon?: string;          // 自定义图标（可选）
  custom_sort: number;           // 自定义排序
  access_count: number;          // 访问次数
  last_access_time?: string;     // 最后访问时间（可选）
}

/**
 * 菜单服务类
 * 提供菜单管理相关的所有API接口封装
 * 包括菜单CRUD操作、用户菜单配置、导入导出等功能
 */
class MenuService {
  /**
   * 获取菜单树结构
   * @returns Promise<MenuNode[]> 返回树形结构的菜单数据
   */
  async getMenuTree() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/tree/`);
    if (!response.ok) {
      throw new Error('获取菜单树失败');
    }
    return response.json();
  }

  /**
   * 获取菜单列表（分页）
   * @param params 查询参数，支持搜索、过滤、分页等
   * @returns Promise<any> 返回分页的菜单列表数据
   */
  async getMenus(params?: any) {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, String(value));
        }
      });
    }
    
    const url = `${API_BASE_URL}/menus/${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    const response = await noAutoLogoutFetch(url);
    if (!response.ok) {
      throw new Error('获取菜单列表失败');
    }
    return response.json();
  }

  /**
   * 获取单个菜单详情
   * @param id 菜单ID
   * @returns Promise<MenuNode> 返回菜单详情数据
   */
  async getMenu(id: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/${id}/`);
    if (!response.ok) {
      throw new Error('获取菜单详情失败');
    }
    return response.json();
  }

  /**
   * 创建新菜单
   * @param data 菜单表单数据
   * @returns Promise<MenuNode> 返回创建的菜单数据
   */
  async createMenu(data: MenuFormData) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '创建菜单失败');
    }
    return response.json();
  }

  /**
   * 更新菜单信息
   * @param id 菜单ID
   * @param data 要更新的菜单数据（部分字段）
   * @returns Promise<MenuNode> 返回更新后的菜单数据
   */
  async updateMenu(id: number, data: Partial<MenuFormData>) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/${id}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '更新菜单失败');
    }
    return response.json();
  }

  /**
   * 删除菜单
   * @param id 菜单ID
   * @returns Promise<any> 返回删除结果
   */
  async deleteMenu(id: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/${id}/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '删除菜单失败');
    }
    return response.json();
  }

  /**
   * 重新排序菜单
   * @param menus 菜单排序数据数组，包含ID、排序号和父菜单ID
   * @returns Promise<any> 返回排序结果
   */
  async reorderMenus(menus: Array<{ id: number; sort_order: number; parent_id?: number }>) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/reorder/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ menus }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '重新排序失败');
    }
    return response.json();
  }

  // 切换菜单可见性
  async toggleVisibility(id: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/${id}/toggle_visibility/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '切换可见性失败');
    }
    return response.json();
  }

  // 切换菜单启用状态
  async toggleEnabled(id: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/${id}/toggle_enabled/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '切换启用状态失败');
    }
    return response.json();
  }

  // 获取权限列表
  async getPermissions() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/permissions/`);
    if (!response.ok) {
      throw new Error('获取权限列表失败');
    }
    return response.json();
  }

  // 获取角色列表
  async getRoles() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/roles/`);
    if (!response.ok) {
      throw new Error('获取角色列表失败');
    }
    return response.json();
  }

  // 获取图标列表
  async getIcons() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/icons/`);
    if (!response.ok) {
      throw new Error('获取图标列表失败');
    }
    return response.json();
  }

  // 获取菜单统计
  async getMenuStats() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/stats/`);
    if (!response.ok) {
      throw new Error('获取菜单统计失败');
    }
    return response.json();
  }

  // 用户菜单配置相关
  
  // 获取用户菜单配置
  async getUserMenuConfigs() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/`);
    if (!response.ok) {
      throw new Error('获取用户菜单配置失败');
    }
    return response.json();
  }

  // 获取收藏菜单
  async getFavoriteMenus() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/favorites/`);
    if (!response.ok) {
      throw new Error('获取收藏菜单失败');
    }
    return response.json();
  }

  /**
   * 切换菜单收藏状态
   * @param configId 用户菜单配置ID
   * @returns Promise<any> 返回切换结果
   */
  async toggleFavorite(configId: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/${configId}/toggle_favorite/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '切换收藏状态失败');
    }
    return response.json();
  }

  // 记录菜单访问
  async recordMenuAccess(menuId: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/${menuId}/access/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '记录菜单访问失败');
    }
    return response.json();
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
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/batch_config/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ configs }),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '批量配置菜单失败');
    }
    return response.json();
  }

  // 创建用户菜单配置
  async createUserMenuConfig(data: Partial<UserMenuConfig>) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '创建用户菜单配置失败');
    }
    return response.json();
  }

  // 更新用户菜单配置
  async updateUserMenuConfig(id: number, data: Partial<UserMenuConfig>) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/${id}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '更新用户菜单配置失败');
    }
    return response.json();
  }

  // 删除用户菜单配置
  async deleteUserMenuConfig(id: number) {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/user-menu-configs/${id}/`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '删除用户菜单配置失败');
    }
    return response.json();
  }

  // 导出菜单配置
  async exportMenus() {
    const response = await fetch(`${API_BASE_URL}/menus/export/`);
    if (!response.ok) {
      throw new Error('导出菜单配置失败');
    }
    return response.blob();
  }

  /**
   * 导入菜单配置
   * @param file 要导入的文件
   * @param options 导入选项
   * @param options.clear_existing 是否清除现有菜单
   * @param options.update_existing 是否更新现有菜单
   * @param options.import_permissions 是否导入权限配置
   * @returns Promise<any> 返回导入结果
   */
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
    
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/import_menus/`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '导入菜单配置失败');
    }
    return response.json();
  }

  // 预热缓存
  async warmCache() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/warm_cache/`, {
      method: 'POST',
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || '预热缓存失败');
    }
    return response.json();
  }

  // 获取性能统计
  async getPerformanceStats() {
    const response = await noAutoLogoutFetch(`${API_BASE_URL}/menus/performance/`);
    if (!response.ok) {
      throw new Error('获取性能统计失败');
    }
    return response.json();
  }
}

export const menuService = new MenuService();