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
    unlockMode: 'pay',
    adUnitId: '',
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
        priceYuan: result.price_fen ? (result.price_fen / 100).toFixed(2) : '0.99',
        unlockMode: result.unlock_mode || 'pay',
        adUnitId: result.ad_unit_id || '',
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
   * 解锁完整报告（付费或广告，由 unlock_mode 决定）
   */
  async unlockReport() {
    if (this.data.paymentLoading) return;

    this.setData({ paymentLoading: true });

    // ── 广告解锁模式：拉起激励视频 ──
    if (this.data.unlockMode === 'ad') {
      this.showRewardedAd();
      return;
    }

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
        const orderNo = payment.order_no;
        wx.requestPayment({
          ...payment.pay_params,
          success: () => {
            // 微信回调可能延迟到账，轮询订单状态直到解锁
            this.waitForUnlock(orderNo);
          },
          fail: () => {
            this.setData({ paymentLoading: false });
            app.handleError(new Error('支付未完成'), true);
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
   * 激励视频广告解锁：拉起广告 → 完整观看后调后端解锁
   */
  showRewardedAd() {
    const adUnitId = this.data.adUnitId;
    if (!adUnitId) {
      this.setData({ paymentLoading: false });
      wx.showToast({ title: '广告位未配置', icon: 'none' });
      return;
    }

    if (!this.rewardedAd) {
      this.rewardedAd = wx.createRewardedVideoAd({ adUnitId });
      this.rewardedAd.onError(() => {});
      this.rewardedAd.onClose((res) => {
        if (res && res.isEnded) {
          // 完整看完 → 调后端解锁
          this.adUnlockResult();
        } else {
          this.setData({ paymentLoading: false });
          wx.showToast({ title: '需完整观看广告才能解锁', icon: 'none' });
        }
      });
    }

    this.rewardedAd.show().catch(() => {
      // 首次无广告缓存 → 重新加载再展示
      this.rewardedAd.load()
        .then(() => this.rewardedAd.show())
        .catch(() => {
          this.setData({ paymentLoading: false });
          wx.showToast({ title: '广告加载失败，请稍后再试', icon: 'none' });
        });
    });
  },

  /**
   * 广告看完 → 调后端广告解锁接口
   */
  async adUnlockResult() {
    try {
      await paymentService.adUnlock(app.globalData.openid, this.data.resultId);
      app.showSuccess('命格已解锁');
      this.setData({ paymentLoading: false });
      setTimeout(() => this.loadResult(), 600);
    } catch (err) {
      this.setData({ paymentLoading: false });
      app.handleError(err);
    }
  },

  /**
   * 支付成功后轮询订单状态（回调可能延迟，最多约15秒）
   */
  waitForUnlock(orderNo, attempt = 0) {
    if (attempt >= 10) {
      this.setData({ paymentLoading: false });
      wx.showToast({ title: '支付处理中，请稍后重新进入查看', icon: 'none' });
      return;
    }
    paymentService
      .queryOrder(orderNo)
      .then((order) => {
        if (order && order.is_paid) {
          this.setData({ paymentLoading: false });
          app.showSuccess('命格已解锁');
          setTimeout(() => this.loadResult(), 600);
        } else {
          setTimeout(() => this.waitForUnlock(orderNo, attempt + 1), 1500);
        }
      })
      .catch(() => {
        setTimeout(() => this.waitForUnlock(orderNo, attempt + 1), 1500);
      });
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