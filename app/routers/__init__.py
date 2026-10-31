"""
路由聚合
"""

from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from .api    import router as api_router
from .static import router as static_router


def get_router(**kwargs) -> APIRouter:
    """
    聚合 API 和 Static 路由并返回。
    """
    router = APIRouter(**kwargs)
    router.include_router(api_router)
    router.include_router(static_router)
    return router
