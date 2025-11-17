from fastapi import APIRouter, Body, Query, HTTPException
from src.service import upload_file
from src.model.response import UploadResponse
import traceback
from loguru import logger


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def api_upload(file_type: int = Query(), file_name: str = Query(), file_bytes: bytes = Body()):
    """上传图片或文件到豆包服务器"""
    try:
        return await upload_file(file_type, file_name, file_bytes)
    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        logger.error(f"详细错误: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成文件失败：{str(e)}")
