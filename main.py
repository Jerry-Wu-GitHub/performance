"""
FastAPI 应用入口

挂载性能监控 API 路由与静态资源路由，并提供开发服务器启动入口。
"""

import uvicorn
from fastapi import FastAPI

# 本地模块
from app.config import HOST, PORT
from app.router import api_router, static_router

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Performance Monitoring",
    description="系统性能监控数据采集，提供 CPU、内存、磁盘、网络、GPU 实时指标",
    version="1.0.0",
)

# 挂载路由
app.include_router(api_router)  # /api/v1/performance/*
app.include_router(static_router)       # / 首页及 /static/* 静态资源

if __name__ == "__main__":
    # 当直接运行此文件时启动 Uvicorn 服务器
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=True,          # 开发时自动重载，生产环境可移除
    )
