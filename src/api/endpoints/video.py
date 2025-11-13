from fastapi import APIRouter, Query, HTTPException
from src.service.video_service import get_video_url
from src.service.video_storage import VideoStorage
from pydantic import BaseModel


router = APIRouter()


class VideoResponse(BaseModel):
  success: bool
  conversation_id: str
  video_count: int
  video_urls: list[str]
  error: str | None = None


class VideoTaskResponse(BaseModel):
  conversation_id: str
  message_id: str
  status: str
  video_urls: list[str]
  retry_count: int
  max_retries: int
  created_at: str
  updated_at: str
  error: str | None = None


@router.get("/get_url", response_model=VideoResponse)
async def api_get_video_url(
  conversation_id: str = Query(..., description="会话ID"),
  message_id: str = Query(None, description="消息ID（可选）"),
  timeout: int = Query(15000, description="超时时间（毫秒）")
):
  """
  从豆包网页获取视频链接
  
  - **conversation_id**: 会话ID（必填）
  - **message_id**: 消息ID（可选）
  - **timeout**: 超时时间，默认15秒
  
  返回视频URL列表
  """
  try:
    result = await get_video_url(conversation_id, message_id, timeout)
    return VideoResponse(**result)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"获取视频链接失败: {str(e)}")


@router.get("/task_status")
async def api_get_video_task_status(
  conversation_id: str = Query(..., description="会话ID"),
  message_id: str = Query(None, description="消息ID（可选）")
):
  """
  查询视频生成任务状态
  
  - **conversation_id**: 会话ID（必填）
  - **message_id**: 消息ID（可选，不提供则返回该会话的所有视频任务）
  
  返回任务状态：
  - **pending**: 等待中
  - **processing**: 处理中
  - **completed**: 已完成
  - **failed**: 失败
  """
  try:
    if message_id:
      # 查询单个任务
      task = VideoStorage.get_task(conversation_id, message_id)
      if not task:
        raise HTTPException(status_code=404, detail="未找到该视频任务")
      return VideoTaskResponse(**task.to_dict())
    else:
      # 查询该会话的所有任务
      tasks = VideoStorage.get_tasks_by_conversation(conversation_id)
      if not tasks:
        raise HTTPException(status_code=404, detail="该会话没有视频任务")
      return {
        "conversation_id": conversation_id,
        "total": len(tasks),
        "tasks": [task.to_dict() for task in tasks]
      }
  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")


@router.get("/all_tasks")
async def api_get_all_video_tasks():
  """
  获取所有视频任务列表
  
  返回所有视频生成任务的状态
  """
  try:
    tasks = VideoStorage.get_all_tasks()
    return {
      "total": len(tasks),
      "tasks": [task.to_dict() for task in tasks]
    }
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")
