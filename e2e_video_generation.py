"""
端到端视频生成示例 (E2E)
一目了然地展示完整的视频生成流程
"""
import requests
import time
from io import BytesIO


BASE_URL = "http://localhost:8000"


def download_image_from_url(image_url: str) -> bytes:
    """从 URL 下载图片"""
    print(f"📥 从 URL 下载图片: {image_url[:60]}...")
    response = requests.get(image_url, timeout=30)
    if response.status_code == 200:
        print(f"✅ 下载成功，大小: {len(response.content)} 字节")
        return response.content
    else:
        raise Exception(f"下载失败: {response.status_code}")


def upload_image(image_data: bytes, filename: str = "image.jpg") -> dict:
    """上传图片到豆包服务器"""
    print(f"📤 上传图片到豆包服务器...")
    
    url = f"{BASE_URL}/api/file/upload"
    params = {
        "file_type": 2,  # 图片类型
        "file_name": filename
    }
    headers = {"Content-Type": "application/octet-stream"}
    
    response = requests.post(url, params=params, data=image_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 上传成功!")
        print(f"   Key: {result['key']}")
        print(f"   Type: {result['type']}")
        return result
    else:
        raise Exception(f"上传失败: {response.text}")


def create_video_task(prompt: str, image_attachment: dict = None) -> dict:
    """创建视频生成任务"""
    video_type = "图生视频" if image_attachment else "文生视频"
    print(f"\n🎬 创建{video_type}任务...")
    print(f"   提示词: {prompt}")
    
    url = f"{BASE_URL}/api/video-gen/generate"
    payload = {
        "prompt": prompt,
        "guest": False
    }
    
    if image_attachment:
        payload["image_attachment"] = image_attachment
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 任务创建成功!")
        print(f"   会话ID: {result['conversation_id']}")
        print(f"   消息ID: {result['message_id']}")
        print(f"   预计时间: {result['estimated_time']}")
        return result
    else:
        raise Exception(f"创建任务失败: {response.text}")


def check_video_status(conversation_id: str, message_id: str) -> dict:
    """查询视频状态"""
    url = f"{BASE_URL}/api/video-gen/status"
    params = {
        "conversation_id": conversation_id,
        "message_id": message_id
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        return response.json()['task']
    else:
        raise Exception(f"查询失败: {response.text}")


def wait_for_video(conversation_id: str, message_id: str, max_wait_minutes: int = 20) -> list:
    """等待视频生成完成"""
    print(f"\n⏳ 等待视频生成...")
    print(f"   提示：首次尝试在3分钟后开始")
    
    start_time = time.time()
    check_interval = 30  # 每30秒检查一次
    last_status = None
    
    while True:
        elapsed = (time.time() - start_time) / 60
        
        if elapsed > max_wait_minutes:
            print(f"\n⏰ 已超过最大等待时间 {max_wait_minutes} 分钟")
            return None
        
        try:
            task = check_video_status(conversation_id, message_id)
            status = task['status']
            retry_count = task['retry_count']
            max_retries = task['max_retries']
            
            # 只在状态变化时打印
            if status != last_status:
                print(f"\n📊 状态更新: {status} (重试 {retry_count}/{max_retries})")
                last_status = status
            else:
                print(f"\r⏳ 等待中... {elapsed:.1f}分钟 | 状态: {status}", end="")
            
            if status == 'completed':
                print(f"\n\n✅ 视频生成完成!")
                print(f"   获取到 {len(task['video_urls'])} 个视频链接:")
                for i, url in enumerate(task['video_urls'], 1):
                    print(f"   {i}. {url}")
                return task['video_urls']
            
            elif status == 'failed':
                print(f"\n\n❌ 视频生成失败")
                if task.get('error'):
                    print(f"   错误: {task['error']}")
                return None
        
        except Exception as e:
            print(f"\n⚠️  查询出错: {str(e)}")
        
        time.sleep(check_interval)


# ============================================================
# E2E 示例 1: 图生视频（本地图片）
# ============================================================
def example_1_image_to_video_local():
    """示例1: 使用本地图片生成视频"""
    print("\n" + "=" * 60)
    print("示例 1: 图生视频（本地图片）")
    print("=" * 60)
    
    # 步骤1: 读取本地图片
    image_path = "gg.jpeg"  # 替换为你的图片路径
    print(f"\n📁 读取本地图片: {image_path}")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        print(f"✅ 读取成功，大小: {len(image_data)} 字节")
    except FileNotFoundError:
        print(f"❌ 文件不存在: {image_path}")
        return
    
    # 步骤2: 上传图片
    attachment = upload_image(image_data, image_path.split('/')[-1])
    
    # 步骤3: 创建视频任务
    prompt = "请将这张图片生成一个5秒的动态视频，保持图片的主要元素"
    result = create_video_task(prompt, attachment)
    
    # 步骤4: 等待视频生成
    video_urls = wait_for_video(result['conversation_id'], result['message_id'])
    
    if video_urls:
        print(f"\n🎉 完成！视频已生成")
    else:
        print(f"\n😔 未能获取到视频")


# ============================================================
# E2E 示例 2: 图生视频（图片链接）
# ============================================================
def example_2_image_to_video_url():
    """示例2: 使用图片链接生成视频"""
    print("\n" + "=" * 60)
    print("示例 2: 图生视频（图片链接）")
    print("=" * 60)
    
    # 步骤1: 从 URL 下载图片
    image_url = "https://example.com/image.jpg"  # 替换为实际的图片链接
    
    # 示例图片链接（可以使用）
    # image_url = "https://picsum.photos/800/600"  # 随机图片
    
    print(f"\n请输入图片链接（直接回车使用示例链接）:")
    user_input = input(f"图片URL [{image_url}]: ").strip()
    if user_input:
        image_url = user_input
    
    try:
        image_data = download_image_from_url(image_url)
    except Exception as e:
        print(f"❌ 下载失败: {str(e)}")
        return
    
    # 步骤2: 上传图片
    filename = image_url.split('/')[-1].split('?')[0] or "image.jpg"
    if not '.' in filename:
        filename = "image.jpg"
    
    attachment = upload_image(image_data, filename)
    
    # 步骤3: 创建视频任务
    prompt = "请将这张图片生成一个5秒的视频，添加一些动态效果"
    result = create_video_task(prompt, attachment)
    
    # 步骤4: 等待视频生成
    video_urls = wait_for_video(result['conversation_id'], result['message_id'])
    
    if video_urls:
        print(f"\n🎉 完成！视频已生成")
    else:
        print(f"\n😔 未能获取到视频")


# ============================================================
# E2E 示例 3: 文生视频
# ============================================================
def example_3_text_to_video():
    """示例3: 纯文本生成视频"""
    print("\n" + "=" * 60)
    print("示例 3: 文生视频（纯文本）")
    print("=" * 60)
    
    # 步骤1: 准备提示词
    prompt = "生成一个海边日落的5秒视频，画面中有海浪轻轻拍打沙滩，天空呈现橙红色"
    
    print(f"\n请输入提示词（直接回车使用示例）:")
    user_input = input(f"提示词 [{prompt}]: ").strip()
    if user_input:
        prompt = user_input
    
    # 步骤2: 创建视频任务（不需要上传图片）
    result = create_video_task(prompt)
    
    # 步骤3: 等待视频生成
    video_urls = wait_for_video(result['conversation_id'], result['message_id'])
    
    if video_urls:
        print(f"\n🎉 完成！视频已生成")
    else:
        print(f"\n😔 未能获取到视频")


# ============================================================
# E2E 示例 4: 快速测试（不等待）
# ============================================================
def example_4_quick_test():
    """示例4: 快速创建任务（不等待完成）"""
    print("\n" + "=" * 60)
    print("示例 4: 快速测试（创建任务后立即返回）")
    print("=" * 60)
    
    # 创建一个文生视频任务
    prompt = "生成一个星空的视频"
    result = create_video_task(prompt)
    
    print(f"\n✅ 任务已创建，可以稍后查询状态")
    print(f"\n📝 查询命令:")
    print(f"   python -c \"import requests; print(requests.get('{BASE_URL}/api/video-gen/status?conversation_id={result['conversation_id']}&message_id={result['message_id']}').json())\"")
    
    print(f"\n或访问:")
    print(f"   {BASE_URL}/api/video-gen/status?conversation_id={result['conversation_id']}&message_id={result['message_id']}")


# ============================================================
# 主菜单
# ============================================================
def main():
    """主菜单"""
    print("\n" + "=" * 60)
    print("豆包视频生成 E2E 示例")
    print("=" * 60)
    print("\n选择要运行的示例:")
    print("1. 图生视频（本地图片）")
    print("2. 图生视频（图片链接）")
    print("3. 文生视频（纯文本）")
    print("4. 快速测试（不等待）")
    print("5. 运行所有示例")
    print("0. 退出")
    
    choice = input("\n请选择 (0-5): ").strip()
    
    if choice == "1":
        example_1_image_to_video_local()
    elif choice == "2":
        example_2_image_to_video_url()
    elif choice == "3":
        example_3_text_to_video()
    elif choice == "4":
        example_4_quick_test()
    elif choice == "5":
        print("\n🚀 运行所有示例...")
        example_1_image_to_video_local()
        time.sleep(2)
        example_2_image_to_video_url()
        time.sleep(2)
        example_3_text_to_video()
        time.sleep(2)
        example_4_quick_test()
    elif choice == "0":
        print("\n👋 再见!")
        return
    else:
        print("\n❌ 无效选项")
        return
    
    print("\n" + "=" * 60)
    print("示例执行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
