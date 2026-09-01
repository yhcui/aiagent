/**
 * 用户服务
 */
const apiService = require('./apiService');

class UserService {
  /**
   * 小程序登录
   */
  async login(code) {
    return apiService.post('/api/auth/login', { code });
  }

  /**
   * 获取用户信息
   */
  async getUserInfo(openid) {
    return apiService.get('/api/auth/user', { openid });
  }

  /**
   * 更新用户信息
   */
  async updateUser(openid, data) {
    return apiService.put('/api/auth/user', { openid, ...data });
  }

  /**
   * 绑定手机号
   */
  async bindPhone(openid, code) {
    return apiService.post('/api/auth/bind-phone', { openid, code });
  }
}

module.exports = new UserService();
