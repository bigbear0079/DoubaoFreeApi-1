"""查询任务状态"""
import requests

conversation_id = "29750692373739266"  # 从日志中看到的

# 先查询这个会话的所有任务
response = requests.get(
    f"http://localhost:8000/api/video-gen/list?conversation_id={conversation_id}"
)

print(f"状态码: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"\n找到 {result['total']} 个任务:")
    for task in result['tasks']:
        print(f"\n任务详情:")
        print(f"  会话ID: {task['conversation_id']}")
        print(f"  消息ID: {task['message_id']}")
        print(f"  状态: {task['status']}")
        print(f"  提示词: {task.get('prompt', 'N/A')}")
        print(f"  重试次数: {task['retry_count']}/{task['max_retries']}")
else:
    print(f"查询失败: {response.text}")
