/**
 * 结果详情页 - 命格揭晓
 */
const app = getApp();
const quizService = require('../../services/quizService');
const paymentService = require('../../services/paymentService');
const { getRoleStyle, rarityLabel } = require('../../utils/roleStyle');

Page({
  data: {
    resultId: null,
    result: null,
    loading: true,
    isPaid: false,
    showPaymentModal: false,
    paymentLoading: false,
    statusBarH: 20,
    roleStyle: null,
    raritySeal: { label: '', cls: 'seal-teal' },
    matchInt: 0,
    unlockCount: 12834,
    priceYuan: '0.99',
  },

  onLoad(options) {
    const resultId = parseInt(options.resultId);
    if (!resultId) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      wx.navigateBack();
      return;
    }

    const sysInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const statusBarH = sysInfo.statusBarHeight || 20;

    this.setData({
      resultId,
      statusBarH,
      unlockCount: 12000 + ((resultId * 137) % 9000),
    });
    this.loadResult();
  },

  goBack() {
    wx.navigateBack({
      fail: () => wx.switchTab({ url: '/pages/index/index' }),
    });
  },

  /**
   * 加载测试结果
   */
  async loadResult() {
    this.setData({ loading: true });

    try {
      const result = await quizService.getResult(this.data.resultId, app.globalData.openid);

      const roleStyle = getRoleStyle(result.role.code);
      const raritySeal = rarityLabel(result.role.rarity);

      this.setData({
        result,
        loading: false,
        isPaid: result.is_paid,
        fullRole: result.full_role,
        roleStyle,
        raritySeal,
        matchInt: Math.round(result.match_score),
        priceYuan: '0.99',
      });

      // 更新分享信息
      this.updateShareInfo(result);
    } catch (err) {
      app.handleError(err);
      setTimeout(() => this.goBack(), 1500);
    }
  },

  /**
   * 更新分享信息
   */
  updateShareInfo(result) {
    const roleName = result.role.name;
    wx.updateShareMenu({
      withShareTicket: true,
      title: `我的命格是「${roleName}」，你也来测测吧！`,
      desc: result.role.description,
    });
  },

  /**
   * 解锁完整报告
   */
  async unlockReport() {
    if (this.data.paymentLoading) return;

    this.setData({ paymentLoading: true });

    try {
      // 创建支付订单
      const payment = await paymentService.createPayment(
        app.globalData.openid,
        this.data.resultId
      );

      // Mock 支付：DEBUG 模式下后端直接标记已支付
      if (payment && payment.mock) {
        app.showSuccess('命格已解锁');
        setTimeout(() => this.loadResult(), 600);
        return;
      }

      // 真实支付：调起微信支付
      if (payment && payment.pay_params) {
        wx.requestPayment({
          ...payment.pay_params,
          success: () => {
            app.showSuccess('命格已解锁');
            setTimeout(() => this.loadResult(), 600);
          },
          fail: () => {
            app.handleError(new Error('支付未完成'), true);
          },
          complete: () => {
            this.setData({ paymentLoading: false });
          },
        });
        return;
      }

      // 未配置支付
      wx.showModal({
        title: '提示',
        content: '支付功能需配置微信支付商户号后才能使用',
        showCancel: false,
      });
    } catch (err) {
      app.handleError(err);
    } finally {
      this.setData({ paymentLoading: false });
    }
  },

  /**
   * 重新测试
   */
  retest() {
    const testId = this.data.result.test_id;
    wx.redirectTo({
      url: `/pages/test/detail?id=${testId}`,
    });
  },

  /**
   * 生成海报
   */
  shareResult() {
    wx.navigateTo({
      url: `/pages/result/share?resultId=${this.data.resultId}`,
    });
  },

  /**
   * 分享给好友
   */
  onShareAppMessage() {
    const result = this.data.result;
    const roleName = result ? result.role.name : '神秘角色';
    return {
      title: `我的命格是「${roleName}」，你也来测测吧！`,
      desc: result ? result.role.description : '',
      path: `/pages/result/detail?resultId=${this.data.resultId}`,
    };
  },
});