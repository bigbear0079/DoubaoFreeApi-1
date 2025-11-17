"""简单测试 - 文生视频（不需要图片）"""
import requests

print("测试文生视频...")
response = requests.post(
    "http://localhost:8000/api/video-gen/generate",
    json={
        "prompt": "卡通娃娃都很开心蹦蹦跳跳",
        "guest": False
    },
    timeout=30
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")
