/**
 * 角色测算小程序 - 入口文件
 */
const userService = require('./services/userService');

App({
  globalData: {
    userInfo: null,
    openid: null,
    isLogin: false,
    apiBaseUrl: 'http://127.0.0.1:8000', // 开发环境
  },

  onLaunch() {
    // 检查登录状态
    this.checkLoginStatus();
  },

  /**
   * 检查登录状态
   */
  async checkLoginStatus() {
    const openid = wx.getStorageSync('openid');
    if (openid) {
      this.globalData.openid = openid;
      this.globalData.isLogin = true;
    }
  },

  /**
   * 小程序登录
   */
  async login() {
    return new Promise((resolve, reject) => {
      wx.login({
        success: async (loginRes) => {
          if (!loginRes.code) {
            reject(new Error('获取code失败'));
            return;
          }

          try {
            const userInfo = await userService.login(loginRes.code);

            this.globalData.userInfo = userInfo;
            this.globalData.openid = userInfo.openid;
            this.globalData.isLogin = true;

            // 保存openid
            wx.setStorageSync('openid', userInfo.openid);
            if (userInfo.nickname) {
              wx.setStorageSync('nickname', userInfo.nickname);
            }
            if (userInfo.avatar) {
              wx.setStorageSync('avatar', userInfo.avatar);
            }

            resolve(userInfo);
          } catch (err) {
            reject(err);
          }
        },
        fail: (err) => {
          reject(err);
        }
      });
    });
  },

  /**
   * 获取用户信息
   */
  getUserInfo() {
    return this.globalData.userInfo;
  },

  /**
   * 更新用户信息
   */
  async updateUserInfo(data) {
    const userInfo = await userService.updateUser(this.globalData.openid, data);
    this.globalData.userInfo = userInfo;
    return userInfo;
  },

  /**
   * 显示加载提示
   */
  showLoading(title = '加载中...') {
    wx.showLoading({
      title,
      mask: true
    });
  },

  /**
   * 隐藏加载提示
   */
  hideLoading() {
    wx.hideLoading();
  },

  /**
   * 显示成功提示
   */
  showSuccess(title = '成功') {
    wx.showToast({
      title,
      icon: 'success',
      duration: 2000
    });
  },

  /**
   * 显示错误提示
   */
  showError(title = '出错了') {
    wx.showToast({
      title,
      icon: 'error',
      duration: 2000
    });
  },

  /**
   * 显示模态对话框
   */
  showModal(options) {
    return new Promise((resolve) => {
      wx.showModal({
        ...options,
        success: (res) => {
          resolve(res);
        }
      });
    });
  },

  /**
   * 错误处理
   */
  handleError(err, showToast = true) {
    console.error('Error:', err);

    let message = '出错了，请重试';
    if (err.message) {
      message = err.message;
    } else if (err.errMsg) {
      message = err.errMsg;
    }

    if (showToast) {
      this.showError(message);
    }

    return message;
  }
});
