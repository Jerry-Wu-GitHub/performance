"""
FastAPI 应用入口

挂载性能监控 API 路由与静态资源路由，并提供开发服务器启动入口。
"""

import uvicorn
from fastapi import FastAPI

# 本地模块
from app import get_config, get_router

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Performance Monitoring",
    description="系统性能监控数据采集，提供 CPU、内存、磁盘、网络、GPU 实时指标",
)
config = get_config()

# 挂载路由
app.include_router(get_router())

if __name__ == "__main__":
    # 当直接运行此文件时启动 Uvicorn 服务器
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=True,          # 开发时自动重载，生产环境可移除
    )
