/**
 * 个人中心页
 */
const app = getApp();

Page({
  data: {
    userInfo: null,
    stats: {
      testCount: 0,
      paidCount: 0
    }
  },

  onShow() {
    this.setData({
      userInfo: app.globalData.userInfo
    });
    this.loadStats();
  },

  /**
   * 加载统计数据
   */
  async loadStats() {
    try {
      const quizService = require('../../services/quizService');
      const history = await quizService.getHistory(app.globalData.openid, 100);

      const paidCount = (history || []).filter(h => h.is_paid).length;

      this.setData({
        stats: {
          testCount: (history || []).length,
          paidCount
        }
      });
    } catch (err) {
      console.error('Load stats failed:', err);
    }
  },

  /**
   * 获取手机号
   */
  async onGetPhoneNumber(e) {
    if (!e.detail.code) return;

    try {
      const userService = require('../../services/userService');
      await userService.bindPhone(app.globalData.openid, e.detail.code);
      app.showSuccess('绑定成功');
      this.setData({ userInfo: app.globalData.userInfo });
    } catch (err) {
      app.handleError(err);
    }
  },

  /**
   * 查看测试历史
   */
  goHistory() {
    wx.switchTab({
      url: '/pages/user/history'
    });
  },

  /**
   * 关于我们
   */
  goAbout() {
    wx.showModal({
      title: '关于我们',
      content: '角色测算小程序 v1.0.0\n\n基于荣格心理学理论，探索你的性格原型',
      showCancel: false
    });
  }
});
