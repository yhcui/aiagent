/**
 * 分享结果页 - 海报预览
 */
const app = getApp();
const posterService = require('../../services/posterService');

Page({
  data: {
    resultId: null,
    posterUrl: '',
    loading: true
  },

  onLoad(options) {
    const resultId = parseInt(options.resultId);
    if (!resultId) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      wx.navigateBack();
      return;
    }

    this.setData({ resultId });
    this.generatePoster();
  },

  /**
   * 生成海报
   */
  async generatePoster() {
    app.showLoading('生成海报...');

    try {
      const poster = await posterService.generatePoster(
        app.globalData.openid,
        this.data.resultId
      );

      if (poster && poster.poster_url) {
        this.setData({
          posterUrl: poster.full_url || (app.globalData.apiBaseUrl + poster.poster_url),
          loading: false
        });
      } else {
        throw new Error('海报生成失败');
      }
    } catch (err) {
      app.handleError(err);
      setTimeout(() => wx.navigateBack(), 1500);
    } finally {
      app.hideLoading();
    }
  },

  /**
   * 保存海报到相册
   */
  savePoster() {
    if (!this.data.posterUrl) return;

    app.showLoading('保存中...');

    wx.downloadFile({
      url: this.data.posterUrl,
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
      },
      complete: () => {
        app.hideLoading();
      }
    });
  },

  /**
   * 分享给好友
   */
  shareToFriend() {
    wx.showShareMenu({
      withShareTicket: true
    });
  },

  /**
   * 关闭页面
   */
  close() {
    wx.navigateBack();
  }
});
