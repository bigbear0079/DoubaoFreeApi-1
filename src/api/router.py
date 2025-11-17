from fastapi import APIRouter
from .endpoints import chat
from .endpoints import file
from .endpoints import video
from .endpoints import video_generation

router = APIRouter()

# 注册各个模块的路由
router.include_router(chat.router, prefix="/chat", tags=["聊天"])
router.include_router(file.router, prefix="/file", tags=["文件"])
router.include_router(video.router, prefix="/video", tags=["视频链接获取"])
router.include_router(video_generation.router, prefix="/video-gen", tags=["视频生成"])