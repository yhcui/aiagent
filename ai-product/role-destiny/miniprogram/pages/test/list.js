/**
 * 测试列表页
 */
const testService = require('../../services/testService');

Page({
  data: {
    testList: [],
    loading: true,
    refreshing: false
  },

  onLoad() {
    this.loadTestList();
  },

  onShow() {
    // 每次显示时刷新
    this.loadTestList();
  },

  /**
   * 加载测试列表
   */
  async loadTestList() {
    if (!this.data.refreshing) {
      this.setData({ loading: true });
    }

    try {
      const testList = await testService.getTestList();
      // 预处理价格数据
      const processedList = (testList || []).map(item => ({
        ...item,
        priceYuan: item.price > 0 ? (item.price / 100).toFixed(2) : '0.00'
      }));
      this.setData({
        testList: processedList,
        loading: false,
        refreshing: false
      });
    } catch (err) {
      console.error('Load test list failed:', err);
      this.setData({ loading: false, refreshing: false });
    }
  },

  /**
   * 进入测试详情
   */
  goTestDetail(e) {
    const testId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/test/detail?id=${testId}`
    });
  },

  /**
   * 下拉刷新
   */
  async onPullDownRefresh() {
    this.setData({ refreshing: true });
    await this.loadTestList();
    wx.stopPullDownRefresh();
  },

  /**
   * 上拉加载更多
   */
  onReachBottom() {
    // 如果有分页需求，可以在这里实现
  }
});
