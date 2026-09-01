/**
 * 答题页面
 */
const app = getApp();
const testService = require('../../services/testService');
const quizService = require('../../services/quizService');

Page({
  data: {
    testId: null,
    test: null,
    currentIndex: 0,
    answers: [],
    selectedOptions: [],
    animating: false,
    canSubmit: false,
    progressPercent: 0
  },

  onLoad(options) {
    const testId = parseInt(options.testId);
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
      const progressPercent = Math.round((1 / test.questions.length) * 100);

      this.setData({
        test,
        answers: new Array(test.questions.length).fill(null),
        progressPercent
      });
    } catch (err) {
      app.handleError(err);
      setTimeout(() => wx.navigateBack(), 1500);
    } finally {
      app.hideLoading();
    }
  },

  /**
   * 更新进度百分比
   */
  updateProgress() {
    const { currentIndex, test } = this.data;
    if (test && test.questions) {
      const progressPercent = Math.round(((currentIndex + 1) / test.questions.length) * 100);
      this.setData({ progressPercent });
    }
  },

  /**
   * 选择选项
   */
  selectOption(e) {
    if (this.data.animating) return;

    const { questionIndex, optionId } = e.currentTarget.dataset;

    const answers = [...this.data.answers];
    answers[questionIndex] = optionId;

    this.setData({
      answers,
      canSubmit: answers.every(a => a !== null)
    });
  },

  /**
   * 下一题
   */
  nextQuestion() {
    if (this.data.animating) return;

    const { currentIndex, test } = this.data;
    if (currentIndex >= test.questions.length - 1) {
      // 最后一题，提交
      this.submitTest();
      return;
    }

    this.setData({ animating: true });

    setTimeout(() => {
      this.setData({
        currentIndex: currentIndex + 1,
        animating: false
      });
      this.updateProgress();
    }, 300);
  },

  /**
   * 上一题
   */
  prevQuestion() {
    if (this.data.animating || this.data.currentIndex === 0) return;

    this.setData({ animating: true });

    setTimeout(() => {
      this.setData({
        currentIndex: this.data.currentIndex - 1,
        animating: false
      });
      this.updateProgress();
    }, 300);
  },

  /**
   * 提交测试
   */
  async submitTest() {
    if (!this.data.canSubmit) {
      app.showToast({ title: '请完成所有题目', icon: 'none' });
      return;
    }

    app.showLoading('提交中...');

    try {
      const result = await quizService.submitTest(
        app.globalData.openid,
        this.data.testId,
        this.data.answers
      );

      // 跳转到结果页
      wx.redirectTo({
        url: `/pages/result/detail?resultId=${result.id}`
      });
    } catch (err) {
      app.handleError(err);
    } finally {
      app.hideLoading();
    }
  },

  /**
   * 退出答题
   */
  exitQuestion() {
    wx.showModal({
      title: '提示',
      content: '确定要退出测试吗？已作答的题目将不会保存',
      success: (res) => {
        if (res.confirm) {
          wx.navigateBack();
        }
      }
    });
  }
});
