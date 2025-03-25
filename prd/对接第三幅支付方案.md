# 第三方 API 对接方案

## 对接背景
对接 PayFast API（HTTPS, API Key + API Key Secret+ HMAC-SHA256），实现支付发起、状态查询、退款。

## 功能需求
### 1. 支付发起
- **端点**: `POST /v1/payments`
- **请求**: `amount` (必填), `currency` (必填), `order_id` (必填), `callback_url` (可选)
- **返回**: `payment_id`, `payment_url`

### 2. 状态查询
- **端点**: `GET /v1/payments/{payment_id}`
- **请求**: `payment_id` (必填)
- **返回**: `status`( pending|success|failed|cancelled ), `amount`, `completed_at`

### 3. 退款
- **端点**: `POST /v1/payments/{payment_id}/refund`
- **请求**: `payment_id` (必填), `amount` (必填), `reason` (可选)
- **返回**: `refund_id`, `status`

## 技术对接
- **Base URL**: `https://api.payfast.com`
- **认证**: API Key + API Key Secret + HMAC-SHA256
- **签名**: `HexEncode(HMAC_SHA256(secret, method + path + query + body))`
- **头部**: `X-API-Key`, `X-Timestamp`, `X-Signature`, `Content-Type`

## 安全性
- **HTTPS**: 强制使用
- **时间戳**: 差距 < 60s
- **错误处理**:
  - **重试**: `5xx`/超时重试 3 次（指数退避：1s, 2s, 4s）
- **监控**: 失败率 > 5% 报警

## 对接流程
1. **准备**: 申请密钥，配置ip白名单
2. **开发**: 实现客户端
3. **测试**: 验证重试
4. **上线**: 灰度发布，监控延迟