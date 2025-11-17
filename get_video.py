"""获取视频链接"""
import requests

conversation_id = "29750692373739266"
message_id = "29717151855266562"

response = requests.get(
    f"http://localhost:8000/api/video-gen/status",
    params={
        "conversation_id": conversation_id,
        "message_id": message_id
    }
)

print(f"状态码: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    task = result['task']
    print(f"\n任务状态: {task['status']}")
    
    if task['status'] == 'completed' and task.get('video_urls'):
        print(f"\n✅ 视频已生成！获取到 {len(task['video_urls'])} 个视频链接:")
        for i, url in enumerate(task['video_urls'], 1):
            print(f"\n视频 {i}:")
            print(url)
    else:
        print(f"\n当前状态: {task['status']}")
        if task.get('error'):
            print(f"错误: {task['error']}")
else:
    print(f"查询失败: {response.text}")
