/**
 * 首页 - 启动和登录页面
 */
const app = getApp();
const testService = require('../../services/testService');

Page({
  data: {
    testList: [],
    loading: true,
    userInfo: null,
    hasLogin: false
  },

  onLoad() {
    this.checkLogin();
  },

  onShow() {
    if (app.globalData.isLogin) {
      this.setData({ hasLogin: true });
    }
  },

  /**
   * 检查登录状态并自动登录
   */
  async checkLogin() {
    if (app.globalData.isLogin) {
      this.setData({
        hasLogin: true,
        userInfo: app.globalData.userInfo
      });
      this.loadTestList();
      return;
    }

    try {
      await this.doLogin();
    } catch (err) {
      console.error('Login failed:', err);
      app.handleError(err, false);
      // 即使登录失败也加载测试列表
      this.loadTestList();
    }
  },

  /**
   * 执行登录
   */
  async doLogin() {
    app.showLoading('登录中...');

    try {
      const userInfo = await app.login();
      this.setData({
        hasLogin: true,
        userInfo
      });
    } catch (err) {
      app.handleError(err, false);
    } finally {
      app.hideLoading();
      this.loadTestList();
    }
  },

  /**
   * 加载测试列表
   */
  async loadTestList() {
    this.setData({ loading: true });

    try {
      const testList = await testService.getTestList();
      // 预处理价格数据，添加 priceYuan 属性用于显示
      const processedList = (testList || []).map(item => ({
        ...item,
        priceYuan: item.price > 0 ? (item.price / 100).toFixed(2) : '0.00'
      }));
      this.setData({
        testList: processedList,
        loading: false
      });
    } catch (err) {
      console.error('Load test list failed:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * 去测试
   */
  goTest(e) {
    const testId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/test/detail?id=${testId}`
    });
  },

  /**
   * 下拉刷新
   */
  async onPullDownRefresh() {
    await this.loadTestList();
    wx.stopPullDownRefresh();
  },

  /**
   * 获取用户信息
   */
  async onGetUserInfo(e) {
    if (!e.detail.userInfo) return;

    const userInfo = e.detail.userInfo;

    try {
      await app.updateUserInfo({
        nickname: userInfo.nickName,
        avatar: userInfo.avatarUrl
      });

      this.setData({ userInfo: app.globalData.userInfo });
      app.showSuccess('授权成功');
    } catch (err) {
      app.handleError(err);
    }
  }
});
