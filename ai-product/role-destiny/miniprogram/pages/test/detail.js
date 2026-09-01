/**
 * 测试详情页
 */
const app = getApp();
const testService = require('../../services/testService');

Page({
  data: {
    testId: null,
    test: null,
    loading: true,
    userInfo: null
  },

  onLoad(options) {
    const testId = options.id;
    if (!testId) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      wx.navigateBack();
      return;
    }

    this.setData({ testId });
    this.loadTestDetail();
  },

  /**
   * 加载测试详情
   */
  async loadTestDetail() {
    app.showLoading('加载中...');

    try {
      const test = await testService.getTestDetail(this.data.testId);
      // 预处理价格数据
      test.priceYuan = test.price > 0 ? (test.price / 100).toFixed(2) : '0.00';
      this.setData({
        test,
        loading: false,
        userInfo: app.globalData.userInfo
      });

      // 更新分享信息
      this.updateShareInfo(test);
    } catch (err) {
      app.handleError(err);
      setTimeout(() => wx.navigateBack(), 1500);
    } finally {
      app.hideLoading();
    }
  },

  /**
   * 更新分享信息
   */
  updateShareInfo(test) {
    wx.updateShareMenu({
      withShareTicket: true,
      title: test.share_title || test.title,
      desc: test.share_desc || test.description,
      imageUrl: test.cover_image
    });
  },

  /**
   * 开始测试
   */
  startTest() {
    // 确保已登录
    if (!app.globalData.isLogin) {
      wx.showModal({
        title: '提示',
        content: '需要先登录才能开始测试',
        success: (res) => {
          if (res.confirm) {
            app.login().then(() => {
              this.goQuestion();
            });
          }
        }
      });
      return;
    }

    this.goQuestion();
  },

  /**
   * 跳转到答题页
   */
  goQuestion() {
    wx.navigateTo({
      url: `/pages/test/question?testId=${this.data.testId}`
    });
  },

  /**
   * 分享给好友
   */
  onShareAppMessage() {
    const test = this.data.test;
    return {
      title: test.share_title || test.title,
      desc: test.share_desc || test.description,
      path: `/pages/test/detail?id=${this.data.testId}`
    };
  }
});
