"""快速测试视频生成功能"""
import requests

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("快速测试视频生成功能")
print("=" * 60)

# 测试文生视频
print("\n🎬 测试文生视频...")
response = requests.post(
    f"{BASE_URL}/api/video-gen/generate",
    json={
        "prompt": "生成一个海边日落的5秒视频",
        "guest": False
    }
)

if response.status_code == 200:
    result = response.json()
    print("✅ 任务创建成功!")
    print(f"   会话ID: {result['conversation_id']}")
    print(f"   消息ID: {result['message_id']}")
    print(f"   状态: {result['task_status']}")
    print(f"   预计时间: {result['estimated_time']}")
    print(f"\n💡 查询状态命令:")
    print(f"   GET {BASE_URL}/api/video-gen/status?conversation_id={result['conversation_id']}&message_id={result['message_id']}")
else:
    print(f"❌ 失败: {response.text}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n下一步:")
print("1. 运行 'python video_gen_demo.py' 使用完整功能")
print("2. 访问 http://localhost:8000/docs 查看 API 文档")
print("3. 阅读 VIDEO_GENERATION_GUIDE.md 了解详细用法")
