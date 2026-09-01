/**
 * 测算服务
 */
const apiService = require('./apiService');

class QuizService {
  /**
   * 提交测试
   */
  async submitTest(openid, testId, answers) {
    return apiService.post('/api/quiz/submit', { openid, test_id: testId, answers });
  }

  /**
   * 获取测试结果
   */
  async getResult(resultId, openid) {
    return apiService.get('/api/quiz/result/' + resultId, { openid });
  }

  /**
   * 获取测试历史
   */
  async getHistory(openid, limit = 10, offset = 0) {
    return apiService.get('/api/quiz/history', { openid, limit, offset });
  }
}

module.exports = QuizService;
