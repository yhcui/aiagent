/**
 * 测试服务
 */
const apiService = require('./apiService');

class TestService {
  /**
   * 获取测试列表
   */
  async getTestList() {
    return apiService.get('/api/tests');
  }

  /**
   * 获取测试详情
   */
  async getTestDetail(testId) {
    return apiService.get(`/api/tests/${testId}`);
  }

  /**
   * 获取分享信息
   */
  async getShareInfo(testId) {
    return apiService.get(`/api/tests/${testId}/share-info`);
  }
}

module.exports = new TestService();
