"""
视频生成功能演示脚本
支持图生视频和文生视频
"""
import requests
import time
import json


BASE_URL = "http://localhost:8000"


def upload_image(image_path: str):
    """上传图片"""
    print(f"\n📤 上传图片: {image_path}")
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    url = f"{BASE_URL}/api/file/upload"
    params = {
        "file_type": 2,  # 图片类型
        "file_name": image_path.split('\\')[-1].split('/')[-1]
    }
    headers = {"Content-Type": "application/octet-stream"}
    
    response = requests.post(url, params=params, data=image_data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 上传成功! Key: {result['key']}")
        return result
    else:
        print(f"❌ 上传失败: {response.text}")
        return None


def generate_video_from_image(image_attachment: dict, prompt: str):
    """图生视频"""
    print(f"\n🎬 创建图生视频任务...")
    print(f"   提示词: {prompt}")
    
    url = f"{BASE_URL}/api/video-gen/generate"
    payload = {
        "prompt": prompt,
        "image_attachment": image_attachment,
        "guest": False
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 任务创建成功!")
        print(f"   会话ID: {result['conversation_id']}")
        print(f"   消息ID: {result['message_id']}")
        print(f"   预计时间: {result['estimated_time']}")
        return result
    else:
        print(f"❌ 创建失败: {response.text}")
        return None


def generate_video_from_text(prompt: str):
    """文生视频"""
    print(f"\n🎬 创建文生视频任务...")
    print(f"   提示词: {prompt}")
    
    url = f"{BASE_URL}/api/video-gen/generate"
    payload = {
        "prompt": prompt,
        "guest": False
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 任务创建成功!")
        print(f"   会话ID: {result['conversation_id']}")
        print(f"   消息ID: {result['message_id']}")
        print(f"   预计时间: {result['estimated_time']}")
        return result
    else:
        print(f"❌ 创建失败: {response.text}")
        return None


def check_video_status(conversation_id: str, message_id: str):
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
        return None


def wait_for_video(conversation_id: str, message_id: str, max_wait_minutes: int = 20):
    """等待视频生成完成"""
    print(f"\n⏳ 等待视频生成（最多 {max_wait_minutes} 分钟）...")
    print(f"   提示：首次查询在3分钟后开始，之后每3分钟重试一次")
    
    start_time = time.time()
    check_interval = 30  # 每30秒检查一次
    
    while True:
        elapsed = (time.time() - start_time) / 60
        
        if elapsed > max_wait_minutes:
            print(f"\n⏰ 已超过最大等待时间")
            break
        
        task = check_video_status(conversation_id, message_id)
        
        if task:
            status = task['status']
            retry_count = task['retry_count']
            max_retries = task['max_retries']
            
            print(f"\r⏳ 状态: {status} | 重试: {retry_count}/{max_retries} | 已等待: {elapsed:.1f}分钟", end="")
            
            if status == 'completed':
                print(f"\n\n✅ 视频生成完成!")
                print(f"   获取到 {len(task['video_urls'])} 个视频链接:")
                for i, url in enumerate(task['video_urls'], 1):
                    print(f"   {i}. {url[:80]}...")
                return task['video_urls']
            
            elif status == 'failed':
                print(f"\n\n❌ 视频生成失败")
                if task.get('error'):
                    print(f"   错误: {task['error']}")
                return None
        
        time.sleep(check_interval)
    
    return None


def list_all_tasks():
    """列出所有视频任务"""
    print(f"\n📋 查询所有视频任务...")
    
    url = f"{BASE_URL}/api/video-gen/list"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        tasks = result['tasks']
        print(f"\n共有 {result['total']} 个任务:")
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. 任务 {task['message_id'][:16]}...")
            print(f"   状态: {task['status']}")
            print(f"   会话: {task['conversation_id']}")
            print(f"   重试: {task['retry_count']}/{task['max_retries']}")
            if task['video_urls']:
                print(f"   视频数: {len(task['video_urls'])}")
        return tasks
    else:
        print(f"❌ 查询失败: {response.text}")
        return None


def main():
    """主菜单"""
    print("=" * 60)
    print("豆包视频生成功能演示")
    print("=" * 60)
    
    while True:
        print("\n请选择功能:")
        print("1. 图生视频 (上传图片 + 提示词)")
        print("2. 文生视频 (仅提示词)")
        print("3. 查询任务状态")
        print("4. 查看所有任务")
        print("5. 退出")
        
        choice = input("\n请输入选项 (1-5): ").strip()
        
        if choice == "1":
            # 图生视频
            image_path = input("\n请输入图片路径: ").strip()
            if not image_path:
                print("❌ 未输入图片路径")
                continue
            
            attachment = upload_image(image_path)
            if not attachment:
                continue
            
            prompt = input("请输入提示词（描述想要的视频效果）: ").strip()
            if not prompt:
                prompt = "请将这张图片生成一个5秒的视频"
            
            result = generate_video_from_image(attachment, prompt)
            if result:
                wait = input("\n是否等待视频生成完成? (y/n): ").strip().lower()
                if wait == 'y':
                    wait_for_video(result['conversation_id'], result['message_id'])
        
        elif choice == "2":
            # 文生视频
            prompt = input("\n请输入提示词（描述想要的视频内容）: ").strip()
            if not prompt:
                print("❌ 未输入提示词")
                continue
            
            result = generate_video_from_text(prompt)
            if result:
                wait = input("\n是否等待视频生成完成? (y/n): ").strip().lower()
                if wait == 'y':
                    wait_for_video(result['conversation_id'], result['message_id'])
        
        elif choice == "3":
            # 查询任务状态
            conv_id = input("\n请输入会话ID: ").strip()
            msg_id = input("请输入消息ID: ").strip()
            
            if conv_id and msg_id:
                task = check_video_status(conv_id, msg_id)
                if task:
                    print(f"\n任务状态:")
                    print(json.dumps(task, indent=2, ensure_ascii=False))
                    
                    if task['status'] == 'pending' or task['status'] == 'processing':
                        wait = input("\n是否等待完成? (y/n): ").strip().lower()
                        if wait == 'y':
                            wait_for_video(conv_id, msg_id)
                else:
                    print("❌ 未找到任务")
        
        elif choice == "4":
            # 查看所有任务
            list_all_tasks()
        
        elif choice == "5":
            print("\n👋 再见!")
            break
        
        else:
            print("❌ 无效选项，请重新选择")


if __name__ == "__main__":
    main()
