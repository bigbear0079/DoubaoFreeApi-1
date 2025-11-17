"""
视频链接存储管理模块
用于存储和查询视频生成任务的状态和链接
"""
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional
from src.service.video_service import get_video_url


# 视频链接存储文件路径
VIDEO_STORAGE_FILE = Path("video_links.json")


class VideoTask:
  """视频任务状态"""
  def __init__(self, conversation_id: str, message_id: str):
    self.conversation_id = conversation_id
    self.message_id = message_id
    self.status = "pending"  # pending, processing, completed, failed
    self.video_urls: list[str] = []
    self.retry_count = 0
    self.max_retries = 10
    self.created_at = datetime.now().isoformat()
    self.updated_at = datetime.now().isoformat()
    self.error: Optional[str] = None

  def to_dict(self):
    return {
      "conversation_id": self.conversation_id,
      "message_id": self.message_id,
      "status": self.status,
      "video_urls": self.video_urls,
      "retry_count": self.retry_count,
      "max_retries": self.max_retries,
      "created_at": self.created_at,
      "updated_at": self.updated_at,
      "error": self.error
    }

  @classmethod
  def from_dict(cls, data: dict):
    task = cls(data["conversation_id"], data["message_id"])
    task.status = data.get("status", "pending")
    task.video_urls = data.get("video_urls", [])
    task.retry_count = data.get("retry_count", 0)
    task.max_retries = data.get("max_retries", 10)
    task.created_at = data.get("created_at", task.created_at)
    task.updated_at = data.get("updated_at", task.updated_at)
    task.error = data.get("error")
    return task


class VideoStorage:
  """视频链接存储管理器"""

  @staticmethod
  def _load_storage() -> dict:
    """加载存储文件"""
    if not VIDEO_STORAGE_FILE.exists():
      return {}
    try:
      with open(VIDEO_STORAGE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
      return {}

  @staticmethod
  def _save_storage(data: dict):
    """保存存储文件"""
    with open(VIDEO_STORAGE_FILE, 'w', encoding='utf-8') as f:
      json.dump(data, f, ensure_ascii=False, indent=2)

  @staticmethod
  def save_task(task: VideoTask):
    """保存任务"""
    storage = VideoStorage._load_storage()
    key = f"{task.conversation_id}_{task.message_id}"
    task.updated_at = datetime.now().isoformat()
    storage[key] = task.to_dict()
    VideoStorage._save_storage(storage)

  @staticmethod
  def get_task(conversation_id: str, message_id: str) -> Optional[VideoTask]:
    """获取任务"""
    storage = VideoStorage._load_storage()
    key = f"{conversation_id}_{message_id}"
    data = storage.get(key)
    if data:
      return VideoTask.from_dict(data)
    return None

  @staticmethod
  def get_tasks_by_conversation(conversation_id: str) -> list[VideoTask]:
    """根据 conversation_id 获取所有相关任务"""
    storage = VideoStorage._load_storage()
    tasks = []
    for data in storage.values():
      if data.get("conversation_id") == conversation_id:
        tasks.append(VideoTask.from_dict(data))
    return tasks

  @staticmethod
  def get_all_tasks() -> list[VideoTask]:
    """获取所有任务"""
    storage = VideoStorage._load_storage()
    return [VideoTask.from_dict(data) for data in storage.values()]


async def fetch_video_task(conversation_id: str, message_id: str, timeout: int = 25000):
  """
  后台任务：定时获取视频链接
  - 每隔3分钟重试一次
  - 最多重试10次
  - 获取成功后停止
  """
  task = VideoStorage.get_task(conversation_id, message_id)
  if not task:
    task = VideoTask(conversation_id, message_id)
    VideoStorage.save_task(task)

  # 等待3分钟后开始第一次尝试
  await asyncio.sleep(180)

  while task.retry_count < task.max_retries:
    try:
      task.status = "processing"
      task.retry_count += 1
      VideoStorage.save_task(task)

      # 调用获取视频链接的API
      result = await get_video_url(conversation_id, message_id, timeout)

      if result["success"] and result["video_urls"]:
        # 成功获取到视频链接
        task.status = "completed"
        task.video_urls = result["video_urls"]
        task.error = None
        VideoStorage.save_task(task)
        print(f"✅ 视频任务完成: {conversation_id} - 获取到 {len(task.video_urls)} 个视频")
        break
      else:
        # 未获取到视频，继续重试
        task.error = result.get("error", "未获取到视频")
        VideoStorage.save_task(task)
        print(f"⏳ 视频任务重试 {task.retry_count}/{task.max_retries}: {conversation_id}")

    except Exception as e:
      task.error = str(e)
      VideoStorage.save_task(task)
      print(f"❌ 视频任务出错 (重试 {task.retry_count}/{task.max_retries}): {str(e)}")

    # 如果还没达到最大重试次数，等待3分钟后继续
    if task.retry_count < task.max_retries:
      await asyncio.sleep(180)

  # 所有重试都失败
  if task.status != "completed":
    task.status = "failed"
    VideoStorage.save_task(task)
    print(f"❌ 视频任务失败: {conversation_id} - 已达到最大重试次数")


def start_video_fetch_task(conversation_id: str, message_id: str, timeout: int = 25000):
  """启动视频获取后台任务"""
  asyncio.create_task(fetch_video_task(conversation_id, message_id, timeout))
  print(f"🎬 启动视频获取任务: {conversation_id} (将在3分钟后开始)")
