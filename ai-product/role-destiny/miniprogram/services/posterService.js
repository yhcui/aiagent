/**
 * 海报服务
 */
const apiService = require('./apiService');

class PosterService {
  /**
   * 生成海报
   */
  async generatePoster(openid, resultId) {
    return apiService.get('/api/poster/generate', { openid, result_id: resultId });
  }
}

module.exports = PosterService;
