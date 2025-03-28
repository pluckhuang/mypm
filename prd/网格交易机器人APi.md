# 产品需求文档 (PRD) - 网格交易机器人V1 API

## 1. 背景与目标

### 1.1 项目背景
加密货币市场的震荡行情为网格交易提供了机会。网格交易通过在固定价格区间内设置买卖网格，利用价格波动赚取差价。现有的交易所 API 使用门槛较高，开发者需要更简单直接的工具来实现这一策略。

### 1.2 产品目标
- 提供 RESTful API，支持开发者快速部署网格交易策略。
- 确保简单易用，适合初级用户。
- 优化执行效率，降低开发和维护成本。
- 目标用户：中小型开发者、个人交易者。

### 1.3 关键指标
- API 调用成功率 > 99%。
- 平均响应时间 < 200ms。
- 30 天内实现正收益（目标 5%）。
- 开发者上手时间 < 1 小时。

---

## 2. 功能需求
### 2.0.1 API 认证方法
```python
import hmac
import hashlib
import time
from typing import Optional, Dict

def generate_signature(
    method: str,
    path: str,
    api_key: str,
    api_secret: str,
    query: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
    timestamp: Optional[int] = None
) -> tuple[str, int]:
    """
    生成 HMAC-SHA512 签名。

    Args:
        method: HTTP 方法（如 "GET", "POST"）
        path: 请求路径（如 "/payments"）
        api_key: API Key
        api_secret: API Secret
        query: 查询参数字典（可选）
        body: 请求体字符串（可选）
        timestamp: Unix 时间戳（可选，默认当前时间）

    Returns:
        tuple: (签名, 时间戳)
    """
    if not all([method, path, api_key, api_secret]):
        raise ValueError("method, path, api_key, and api_secret are required")

    method = method.upper()
    path = path.strip('/')
    query_string = '&'.join(f"{k}={v}" for k, v in sorted((query or {}).items())) if query else ""
    body = body or ""
    timestamp = timestamp or int(time.time())

    body_hash = hashlib.sha512(body.encode('utf-8')).hexdigest()
    signature_string = f"{method}|{path}|{query_string}|{body_hash}|{timestamp}|{api_key}"

    signature = hmac.new(
        api_secret.encode('utf-8'),
        signature_string.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()

    return signature, timestamp
```
#### 服务器签证
```python
def verify_signature(method, path, api_key, query, body, timestamp, signature):
    secret = get_secret(api_key)  # 从数据库获取
    expected_sign, _ = generate_signature(method, path, api_key, secret, query, body, int(timestamp))
    if abs(time.time() - int(timestamp)) > 60:
        return False
    return hmac.compare_digest(expected_sign, signature)
```


### 2.1 核心功能

#### 2.1.1 创建网格策略
- **描述**：用户通过 API 创建静态网格策略，指定交易对、价格区间和网格数量。
- **接口**：# 全部接口权限假定使用消息认证

```
POST /v1/spot/grid/strategies
Header:
{
    "X-API-Key": api_key,
    "X-Timestamp": ts,
    "X-Signature": sign,
    "Content-Type": "application/json"
}
Body:
{
    "symbol": "BTC/USDT",        // 交易对
    "lower_price": 55000.0,      // 最低价格
    "upper_price": 65000.0,      // 最高价格
    "grid_count": 10,            // 网格数量
    "amount_per_grid": 0.001     // 每网格交易量 (BTC)
}
Response (201 Created):
{
    "strategy_id": "grid_12345",
    "created_at": "2025-03-27T10:00:00Z"
}
```

#### 2.1.2 查询策略状态
- **描述**：返回策略的运行状态、网格执行情况和收益。
- **接口**：
```
GET /v1/grid/strategies/{strategy_id}
Header:
{
    "X-API-Key": api_key,
    "X-Timestamp": ts,
    "X-Signature": sign,
    "Content-Type": "application/json"
}
Response (200 OK):
{
    "strategy_id": "grid_12345",
    "symbol": "BTC/USDT",
    "status": "running",
    "grids": {
        "buy": {"55000": {"held": true}, "56000": {"held": false}},
        "sell": {"56000": {"held": false}, "57000": {"held": true}}
    },
    "profit": 75.50,          // USDT
    "updated_at": "2025-03-27T12:00:00Z"
}
```

#### 2.1.3 停止策略
- **描述**：停止策略并取消未执行订单。
- **接口**：
```
DELETE /v1/grid/strategies/{strategy_id}
Header:
{
    "X-API-Key": api_key,
    "X-Timestamp": ts,
    "X-Signature": sign,
    "Content-Type": "application/json"
}
Response (200 OK):
{
    "strategy_id": "grid_12345",
    "status": "stopped"
}
```


### 2.2 非功能需求
- **安全性**：API Key + HMAC-SHA512 签名，支持 IP 白名单。
- **性能**：支持每秒 100 次请求，延迟 < 200ms。
---

## 3. 用户场景

### 3.1 典型用户
- **画像**：懂基础编程，有一定交易量的技术交易者。
- **需求**：在 BTC/USDT 上实现简单网格交易，赚取稳定收益。

### 3.2 使用流程
1. 用户调用 POST 接口创建策略（55000-65000 美元，10 个网格）。
2. 系统初始化固定网格，通过 WebSocket 监控价格，自动触发买卖。
3. 用户通过 GET 接口查看收益和状态。
4. 若需调整，用户调用 DELETE 接口停止策略。

---

## 4. 设计与实现

### 4.1 系统架构(略)

### 4.2 网格交易逻辑
#### 4.2.1 初始化网格
- **输入**：`lower_price=55000`, `upper_price=65000`, `grid_count=10`, `amount_per_grid=0.001`。
- **计算**：
  - 间隔：`(65000 - 55000) / 10 = 1000 美元`。
  - 买入网格：55000, 56000, ..., 64000。
  - 卖出网格：56000, 57000, ..., 65000。
- **存储**：`buy_grids` 和 `sell_grids`，每个网格包含 `{held: bool, order_id: string}
  - 买入网格表示是否持有订单, 卖出网格表示是否有卖单等待卖出。

#### 4.2.2 实时价格监控
- **数据源** 比如内部服务 WebSocket（`wss://api.gateio.ws/ws/v4/`）。
- **逻辑**：
  - 获取最新价格（如 59800）。
  - 检查触发条件。

#### 4.2.3 触发与执行
- **买入**：
  - 条件：`current_price <= buy_price` 且未持有。
  - 动作：以网格点价格（如 59000）下限价买单，补挂卖单（如 60000）。
  - 状态：`buy_grids[59000]["held"] = True`, `sell_grids[60000]["held"] = True`。
- **卖出**：
  - 条件：`current_price >= sell_price` 且已持有。
  - 动作：以网格点价格（如 61000）下限价卖单，补挂买单（如 60000）。
  - 状态：`sell_grids[61000]["held"] = False`。
  - 收益：`profit += (sell_price - buy_price) * 0.001 - sell_price * 0.001 * 0.001`。

### 4.3 数据模型
- **Strategy**：
  - `strategy_id` (string)
  - `symbol` (string)
  - `lower_price` (float)
  - `upper_price` (float)
  - `grid_count` (int)
  - `amount_per_grid` (float)
  - `status` (string)
  - `profit` (float)
- **Grids**：
  - `buy_grids`: `{price: {"held": bool, "order_id": string}}`
  - `sell_grids`: `{price: {"held": bool, "order_id": string}}`

### 4.4 错误处理
- **400 Bad Request**：参数无效。
- **401 Unauthorized**：签名错误。
- **429 Too Many Requests**：超出限流。
- **503 Service Unavailable** API 不可用，重试 3 次。

---

## 5. 竞品分析

### 5.1 竞品
- **Binance Grid Trading**：内置功能，API 不开放。


### 5.2 差异化策略
- 免费基础 API，简单易用。
- 固定网格，适合震荡行情。

---

## 6. 实施计划

### 6.1 时间表

### 6.2 资源需求

---

## 7. 数据分析与优化

### 7.1 关键指标
- **调用频率**：每分钟请求数。
- **响应时间**：平均延迟。
- **错误率**：失败请求占比。
- **收益**：净利。

### 7.2 优化方向
- 延迟 > 200ms：增加缓存。
- 错误率 > 1%：调整请求频率。

---

## 8. 风险与应对

### 8.1 风险
- **单边行情**：价格超出区间导致亏损。
- **应对**：提示用户设置合理区间，建议手动停止。
---

## 9. 附录

### 9.1 示例代码
```python
import requests

# 创建策略
url = "https://api.example.com/v1/grid/strategies"
headers = {
    "X-API-Key": api_key,
    "X-Timestamp": ts,
    "X-Signature": sign,
    "Content-Type": "application/json"
}
data = {
    "symbol": "BTC/USDT",
    "lower_price": 55000.0,
    "upper_price": 65000.0,
    "grid_count": 10,
    "amount_per_grid": 0.001
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```
### 9.2 执行逻辑伪代码

```
以下是网格交易中买卖的触发与执行逻辑，包含详细的触发条件、执行步骤和异常失败的处理机制，确保健壮性和状态一致性。

---

## 1. 触发条件
触发条件判断是否启动买入或卖出操作，依赖实时市场价格和网格状态。

### 1.1 买入触发条件
- **条件**：
  - `current_price <= buy_price`：当前市场价格小于或等于买入网格价格。
  - `not held`：该网格点未持有仓位（`held = False`）。
- **意义**：
  - 价格下跌到预设低点时触发买入，符合“低买高卖”策略。
  - 避免重复买入，确保每个网格点只持一个仓位。

### 1.2 卖出触发条件
- **条件**：
  - `current_price >= sell_price`：当前市场价格大于或等于卖出网格价格。
  - `held`：该网格点已持有仓位（`held = True`）。
- **意义**：
  - 价格上涨到预设高点时触发卖出，实现差价收益。
  - 确保只卖出已持有的仓位，维持交易循环。

---

## 2. 执行过程
执行过程包括下单、状态更新和补挂订单，加入异常处理以应对失败情况。

### 2.1 买入执行过程
#### 触发条件
- `current_price <= buy_price` 且 `not held`。

#### 执行步骤
1. **条件检查**：
   - 遍历所有买入网格（如 `buy_grids`）。
   - 示例：`current_price = 57900`，`buy_price = 58000`，`held = False`，触发。

2. **下单尝试**：
   - 以 `buy_price`（如 58000）下限价单。
   - 参数：`symbol="BTC/USDT"`, `side="BUY"`, `type="LIMIT"`, `price=58000`, `quantity=0.001`。
   - **异常处理**：
     - 重试 3 次，每次间隔 1 秒。
     - 成功：获取 `order_id`。
     - 失败：记录错误，尝试取消订单，不更新状态。

3. **状态更新**：
   - 成功：`buy_grids[58000]["held"] = True`，记录 `order_id`。
   - 失败：保持 `held = False`，回滚任何临时状态。
   - 提交数据库（PostgreSQL）。

4. **补挂卖单**：
   - 计算 `sell_price = buy_price + step`（如 58000 + 1000 = 59000）。
   - 下单：限价卖单 59000。
   - **异常处理**：
     - 成功：`sell_grids[59000]["held"] = True`。
     - 失败：回滚买入状态（`buy_grids[58000]["held"] = False`），取消买单。
   - 提交数据库。
```

### 9.3 接口文档标准
- **使用 Swagger 生成。**
- **包含参数说明、响应示例、错误码。**
- [link](../swagger/grid_trading.yaml)
