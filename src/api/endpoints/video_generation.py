"""
视频生成 API 接口
支持图生视频和文生视频
"""
from fastapi import APIRouter, Body, Query, HTTPException
from pydantic import BaseModel
from src.service import chat_completion, upload_file
from src.service.video_storage import start_video_fetch_task, VideoStorage
from src.model.response import CompletionResponse
import httpx


router = APIRouter()


class VideoGenerationRequest(BaseModel):
    """视频生成请求"""
    prompt: str  # 提示词
    image_attachment: dict | None = None  # 图片附件（图生视频时使用）
    image_url: str | None = None  # 图片链接（自动下载并上传）
    guest: bool = False  # 是否使用游客账号
    conversation_id: str | None = None  # 会话ID（可选）
    section_id: str | None = None  # 段落ID（可选）


class VideoGenerationResponse(BaseModel):
    """视频生成响应"""
    success: bool
    message: str
    conversation_id: str
    message_id: str
    section_id: str
    task_status: str  # pending, processing, completed, failed
    estimated_time: str  # 预计完成时间


@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_video(request: VideoGenerationRequest = Body()):
    """
    生成视频（支持图生视频和文生视频）
    
    **图生视频方式1 - 使用已上传的图片：**
    - 先调用 `/api/file/upload` 上传图片（file_type=2）
    - 将返回的附件信息传入 `image_attachment` 参数
    
    **图生视频方式2 - 使用图片链接：**
    - 直接提供 `image_url` 参数（图片链接）
    - 系统自动下载并上传图片
    
    **文生视频：**
    - 只需提供提示词 `prompt`
    - 不传 `image_attachment` 和 `image_url` 参数
    
    **返回：**
    - 立即返回任务信息
    - 后台自动开始获取视频（3分钟后开始，每3分钟重试一次）
    - 通过 `/api/video-gen/status` 查询视频生成状态
    
    **示例1 - 使用已上传的图片：**
    ```json
    {
        "prompt": "请将这张图片生成一个5秒的视频",
        "image_attachment": {
            "key": "tos-cn-i-xxx/xxx.jpeg",
            "name": "image.jpeg",
            "type": "vlm_image",
            "file_review_state": 3,
            "file_parse_state": 3,
            "identifier": "xxx"
        },
        "guest": false
    }
    ```
    
    **示例2 - 使用图片链接：**
    ```json
    {
        "prompt": "请将这张图片生成一个5秒的视频",
        "image_url": "https://example.com/image.jpg",
        "guest": false
    }
    ```
    
    **示例3 - 文生视频：**
    ```json
    {
        "prompt": "生成一个海边日落的5秒视频",
        "guest": false
    }
    ```
    """
    try:
        # 准备附件列表
        attachments = []
        
        # 如果提供了图片链接，先下载并上传
        if request.image_url:
            try:
                # 下载图片（自动跟随重定向）
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    response = await client.get(request.image_url)
                    if response.status_code != 200:
                        raise HTTPException(status_code=400, detail=f"下载图片失败: HTTP {response.status_code}")
                    image_data = response.content
                
                # 从 URL 提取文件名
                filename = request.image_url.split('/')[-1].split('?')[0]
                if not '.' in filename:
                    filename = "image.jpg"
                
                # 上传图片
                attachment = await upload_file(2, filename, image_data)
                attachments.append(attachment.dict() if hasattr(attachment, 'dict') else attachment)
                
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"处理图片链接失败: {str(e)}")
        
        # 如果提供了已上传的图片附件
        elif request.image_attachment:
            attachments.append(request.image_attachment)
        
        # 调用聊天接口，content_type=2020 表示视频生成
        text, imgs, conv_id, msg_id, sec_id = await chat_completion(
            prompt=request.prompt,
            guest=request.guest,
            conversation_id=request.conversation_id,
            section_id=request.section_id,
            attachments=attachments,
            use_auto_cot=False,
            use_deep_think=False,
            content_type=2020  # 视频生成类型
        )
        
        # 启动后台任务获取视频链接
        start_video_fetch_task(conv_id, msg_id, timeout=25000)
        
        return VideoGenerationResponse(
            success=True,
            message="视频生成任务已创建，正在处理中...",
            conversation_id=conv_id,
            message_id=msg_id,
            section_id=sec_id,
            task_status="pending",
            estimated_time="预计3-15分钟完成"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建视频生成任务失败: {str(e)}")


@router.get("/status")
async def get_video_status(
    conversation_id: str = Query(..., description="会话ID"),
    message_id: str = Query(..., description="消息ID")
):
    """
    查询视频生成状态
    
    **返回状态：**
    - `pending`: 等待中（任务已创建，等待首次尝试）
    - `processing`: 处理中（正在尝试获取视频）
    - `completed`: 已完成（视频已生成，可获取链接）
    - `failed`: 失败（达到最大重试次数）
    
    **示例：**
    ```
    GET /api/video-gen/status?conversation_id=xxx&message_id=xxx
    ```
    """
    try:
        task = VideoStorage.get_task(conversation_id, message_id)
        if not task:
            raise HTTPException(status_code=404, detail="未找到该视频任务")
        
        return {
            "success": True,
            "task": task.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")


@router.get("/list")
async def list_video_tasks(
    conversation_id: str = Query(None, description="会话ID（可选，不提供则返回所有任务）")
):
    """
    获取视频任务列表
    
    **参数：**
    - `conversation_id`: 可选，指定会话ID则只返回该会话的任务
    
    **示例：**
    ```
    GET /api/video-gen/list
    GET /api/video-gen/list?conversation_id=xxx
    ```
    """
    try:
        if conversation_id:
            tasks = VideoStorage.get_tasks_by_conversation(conversation_id)
        else:
            tasks = VideoStorage.get_all_tasks()
        
        return {
            "success": True,
            "total": len(tasks),
            "tasks": [task.to_dict() for task in tasks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")
