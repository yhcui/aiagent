/**
 * 首页 - 命格宫殿
 */
const app = getApp();
const testService = require('../../services/testService');
const { ROLE_STYLES, GATE_EMBLEMS, getRoleStyle } = require('../../utils/roleStyle');

const GUEST_NAMES = ['阿橘', '拾月', '苏苏', '晚晚', '糖糖', '初七', '小时', '软软', '眠眠', '青禾'];

Page({
  data: {
    testList: [],
    loading: true,
    statusBarH: 20,
    gateEmblems: [],
    tickerText: '',
    firstTest: null,
  },

  onLoad() {
    const sysInfo = wx.getWindowInfo ? wx.getWindowInfo() : wx.getSystemInfoSync();
    const statusBarH = sysInfo.statusBarHeight || 20;

    // 月门徽记（取三个视觉搭配的角色）
    const gateEmblems = GATE_EMBLEMS.map((code, idx) => ({
      code,
      cls: `p${idx}`,
      delay: idx * 0.9,
      style: getRoleStyle(code),
    }));

    this.setData({ statusBarH, gateEmblems });
    this.startTicker();
    this.checkLogin();
  },

  onShow() {
    if (app.globalData.isLogin && !this.data.firstTest) {
      this.loadTestList();
    }
  },

  onUnload() {
    this.stopTicker();
  },

  /**
   * 滚动播报（宫廷坊间传闻）
   */
  startTicker() {
    const roles = Object.keys(ROLE_STYLES).map((k) => ROLE_STYLES[k].name);
    const pool = [];
    for (let i = 0; i < 8; i++) {
      const name = GUEST_NAMES[i % GUEST_NAMES.length];
      const role = roles[(i * 5 + 2) % roles.length];
      pool.push(`${name}刚刚测出了「${role}」`);
    }

    let idx = 0;
    this.tickerTimer = setInterval(() => {
      idx = (idx + 1) % pool.length;
      this.setData({ tickerText: pool[idx] });
    }, 3600);

    this.setData({ tickerText: pool[0] });
  },

  stopTicker() {
    if (this.tickerTimer) {
      clearInterval(this.tickerTimer);
      this.tickerTimer = null;
    }
  },

  /**
   * 检查登录状态并自动登录
   */
  async checkLogin() {
    if (app.globalData.isLogin) {
      this.loadTestList();
      return;
    }

    try {
      await app.login();
    } catch (err) {
      console.error('Login failed:', err);
    } finally {
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
      const processedList = (testList || []).map((item) => ({
        ...item,
        priceYuan: item.price > 0 ? (item.price / 100).toFixed(2) : '0.00',
      }));
      this.setData({
        testList: processedList,
        firstTest: processedList[0] || null,
        loading: false,
      });
    } catch (err) {
      console.error('Load test list failed:', err);
      this.setData({ loading: false });
    }
  },

  /**
   * 直接开始第一个测算
   */
  startTest() {
    const first = this.data.firstTest;
    if (first) {
      this.goTest({ currentTarget: { dataset: { id: first.id } } });
    } else {
      app.showError('测算尚未备好');
    }
  },

  /**
   * 去测试
   */
  goTest(e) {
    const testId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/test/detail?id=${testId}`,
    });
  },

  /**
   * 去测试列表 Tab
   */
  goTestList() {
    wx.switchTab({
      url: '/pages/test/list',
    });
  },
});