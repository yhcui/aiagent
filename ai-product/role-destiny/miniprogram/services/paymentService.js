/**
 * 支付服务
 */
const apiService = require('./apiService');

class PaymentService {
  /**
   * 创建支付订单
   */
  async createPayment(openid, resultId) {
    return apiService.post('/api/payment/create', { openid, result_id: resultId });
  }

  /**
   * 查询订单状态
   */
  async queryOrder(orderNo) {
    return apiService.get('/api/payment/query/' + orderNo);
  }
}

module.exports = PaymentService;
