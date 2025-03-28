# pip install websocket-client
import json
import time

from websocket import create_connection

# 建立 WebSocket 连接
ws = create_connection("wss://api.gateio.ws/ws/v4/")

# 构造订阅请求
subscribe_msg = {
    "time": int(time.time()),
    "channel": "spot.tickers",
    "event": "subscribe",
    "payload": ["BTC_USDT"]
}

# 发送订阅请求
ws.send(json.dumps(subscribe_msg))

# 接收并解析数据
while True:
    response = ws.recv()
    data = json.loads(response)
    if data.get("event") == "update" and data.get("channel") == "spot.tickers":
        result = data["result"]
        current_price = result["last"]
        print(f"BTC_USDT 当前价格: {current_price}")
#       BTC_USDT 当前价格: 86092.4
    elif data.get("event") == "subscribe":
        print("订阅成功:", data)
#         订阅成功:
# {
# 	'time': 1743138611,
# 	'time_ms': 1743138611763,
# 	'conn_id': 'bb7fe401a66d36f0',
# 	'trace_id': 'dc5863cf6a410bf3634847babf43f933',
# 	'channel': 'spot.tickers',
# 	'event': 'subscribe',
# 	'payload': ['BTC_USDT'],
# 	'result': {
# 		'status': 'success'
# 	},
# 	'requestId': 'dc5863cf6a410bf3634847babf43f933'
# }

# 关闭连接（实际运行时可根据需要移除）
ws.close()

