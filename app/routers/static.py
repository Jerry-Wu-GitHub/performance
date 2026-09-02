"""
静态首页路由
"""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette import status

from ..config import INDEX_PATH, STATIC_DIR


router = APIRouter(tags=["Performance Static"])

# 挂载整个静态目录，提供 /static/* 访问
@router.get("/static/{full_path:path}", status_code=status.HTTP_200_OK)
async def serve_static(full_path: str):
    """
    返回前端文件。
    """
    # 尝试返回具体文件
    file_path = STATIC_DIR / full_path
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"detail": "File not exist"}


# 主页
@router.get("/")
async def serve_index() -> FileResponse:
    """
    提供前端首页 HTML 文件。

    该路由对应 `GET /`，返回 `static/html/index.html` 文件。
    用于承载监控面板的前端界面。
    """
    return FileResponse(INDEX_PATH)
