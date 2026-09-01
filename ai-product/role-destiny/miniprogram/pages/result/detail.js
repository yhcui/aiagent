/**
 * 结果详情页
 */
const app = getApp();
const quizService = require('../../services/quizService');
const paymentService = require('../../services/paymentService');

Page({
  data: {
    resultId: null,
    result: null,
    loading: true,
    isPaid: false,
    showPaymentModal: false,
    paymentLoading: false
  },

  onLoad(options) {
    const resultId = parseInt(options.resultId);
    if (!resultId) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      wx.navigateBack();
      return;
    }

    this.setData({ resultId });
    this.loadResult();
  },

  /**
   * 加载测试结果
   */
  async loadResult() {
    app.showLoading('加载中...');

    try {
      const result = await quizService.getResult(this.data.resultId, app.globalData.openid);

      this.setData({
        result,
        loading: false,
        isPaid: result.is_paid
      });

      // 更新分享信息
      this.updateShareInfo(result);
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
  updateShareInfo(result) {
    const roleName = result.role.name;
    wx.updateShareMenu({
      withShareTicket: true,
      title: `我的角色是「${roleName}」，你也来测测吧！`,
      desc: result.role.description,
      imageUrl: result.role.image
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

      // 调用微信支付（实际需要使用wx.requestPayment）
      // 这里简化处理，直接模拟支付成功
      wx.showModal({
        title: '提示',
        content: '支付功能需要配置微信支付商户号',
        showCancel: false
      });

      this.setData({ paymentLoading: false });

    } catch (err) {
      app.handleError(err);
      this.setData({ paymentLoading: false });
    }
  },

  /**
   * 重新测试
   */
  retest() {
    const testId = this.data.result.test_id;
    wx.redirectTo({
      url: `/pages/test/detail?id=${testId}`
    });
  },

  /**
   * 分享结果
   */
  shareResult() {
    wx.navigateTo({
      url: `/pages/result/share?resultId=${this.data.resultId}`
    });
  },

  /**
   * 保存海报
   */
  async savePoster() {
    app.showLoading('生成海报...');

    try {
      const posterService = require('../../services/posterService');
      const poster = await posterService.generatePoster(
        app.globalData.openid,
        this.data.resultId
      );

      if (poster && poster.poster_url) {
        // 下载海报
        const fullUrl = poster.full_url || (app.globalData.apiBaseUrl + poster.poster_url);

        wx.downloadFile({
          url: fullUrl,
          success: (res) => {
            if (res.statusCode === 200) {
              wx.saveImageToPhotosAlbum({
                filePath: res.tempFilePath,
                success: () => {
                  app.showSuccess('海报已保存到相册');
                },
                fail: (err) => {
                  if (err.errMsg.includes('auth deny')) {
                    wx.showModal({
                      title: '提示',
                      content: '需要您授权保存图片到相册',
                      success: (res) => {
                        if (res.confirm) {
                          wx.openSetting();
                        }
                      }
                    });
                  } else {
                    app.handleError(err);
                  }
                }
              });
            }
          },
          fail: (err) => {
            app.handleError(err);
          }
        });
      }
    } catch (err) {
      app.handleError(err);
    } finally {
      app.hideLoading();
    }
  },

  /**
   * 分享给好友
   */
  onShareAppMessage() {
    const result = this.data.result;
    const roleName = result?.role?.name || '神秘角色';
    return {
      title: `我的角色是「${roleName}」，你也来测测吧！`,
      desc: result?.role?.description,
      path: `/pages/result/detail?resultId=${this.data.resultId}`
    };
  }
});
