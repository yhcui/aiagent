/**
 * 测试历史记录页 - 命格卷宗
 */
const app = getApp();
const quizService = require('../../services/quizService');
const { getRoleStyle } = require('../../utils/roleStyle');

Page({
  data: {
    historyList: [],
    loading: true,
    refreshing: false,
    empty: false
  },

  onShow() {
    this.loadHistory();
  },

  /**
   * 加载历史记录
   */
  async loadHistory() {
    if (!this.data.refreshing) {
      this.setData({ loading: true });
    }

    try {
      const history = await quizService.getHistory(
        app.globalData.openid,
        20,
        0
      );

      const historyList = (history || []).map((item) => ({
        ...item,
        roleStyle: getRoleStyle(item.role_code),
      }));

      this.setData({
        historyList,
        loading: false,
        refreshing: false,
        empty: !historyList.length
      });
    } catch (err) {
      console.error('Load history failed:', err);
      this.setData({ loading: false, refreshing: false });
    }
  },

  /**
   * 查看结果详情
   */
  goResult(e) {
    const resultId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/result/detail?resultId=${resultId}`
    });
  },

  /**
   * 去测算
   */
  goTest() {
    wx.switchTab({
      url: '/pages/index/index'
    });
  },

  /**
   * 下拉刷新
   */
  async onPullDownRefresh() {
    this.setData({ refreshing: true });
    await this.loadHistory();
    wx.stopPullDownRefresh();
  }
});
