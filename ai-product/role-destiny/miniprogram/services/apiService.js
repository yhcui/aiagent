/**
 * API服务层
 */
class ApiService {
  constructor() {
    // 延迟获取 app 实例，避免在模块加载时 app 还未初始化
  }

  get baseUrl() {
    const app = getApp();
    return app?.globalData?.apiBaseUrl || '';
  }

  /**
   * 发送请求
   */
  request(options) {
    return new Promise((resolve, reject) => {
      const { url, method = 'GET', data, header = {} } = options;

      // 添加默认header
      const defaultHeader = {
        'Content-Type': 'application/json'
      };

      wx.request({
        url: `${this.baseUrl}${url}`,
        method,
        data,
        header: { ...defaultHeader, ...header },
        success: (res) => {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else if (res.statusCode === 401) {
            // 未授权，跳转登录
            wx.navigateTo({ url: '/pages/index/index' });
            reject(new Error('请先登录'));
          } else {
            const error = res.data?.detail || res.data?.message || '请求失败';
            reject(new Error(error));
          }
        },
        fail: (err) => {
          console.error('Request failed:', err);
          reject(new Error('网络请求失败，请检查网络连接'));
        }
      });
    });
  }

  /**
   * GET请求
   */
  get(url, params) {
    let queryString = '';
    if (params) {
      queryString = '?' + Object.entries(params)
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&');
    }
    return this.request({ url: url + queryString, method: 'GET' });
  }

  /**
   * POST请求
   */
  post(url, data) {
    return this.request({ url, method: 'POST', data });
  }

  /**
   * PUT请求
   */
  put(url, data) {
    return this.request({ url, method: 'PUT', data });
  }
}

// 导出单例
module.exports = new ApiService();
