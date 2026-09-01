"""
API 路由：性能监控数据采集接口
"""

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette import status

from .config import MEASUREMENT_INTERVAL, INDEX_PATH, STATIC_DIR
from .common import (
    cpu_stats_collector,
    memory_stats_collector,
    disk_stats_collector,
    network_stats_collector,
    gpu_stats_collector,
)
from .schemas import (
    ApiResponse,
    CPUStats,
    MemoryStats,
    DiskStats,
    NetworkStats,
    GPUStats,
    collect_cpu_stats,
    collect_memory_stats,
    collect_disk_stats,
    collect_network_stats,
    collect_gpu_stats,
)

api_router = APIRouter(prefix="/api/v1/performance", tags=["Performance API"])


@api_router.get("/cpu", status_code=status.HTTP_200_OK, response_model=ApiResponse[CPUStats])
async def get_cpu_stats() -> ApiResponse[CPUStats]:
    """
    获取当前 CPU 状态数据。

    采集内容包括：
        - 物理/逻辑核心数、频率
        - 整体与每核心使用率
        - 系统负载平均值（Unix 平台）
        - 进程总数、系统运行时间
        - 上下文切换、中断等累计计数

    Returns:
        ApiResponse[CPUStats]: 统一响应外壳，data 字段包含 CPUStats 模型。
    """
    stats = await collect_cpu_stats(cpu_stats_collector, interval=MEASUREMENT_INTERVAL)
    return ApiResponse(data=stats)


@api_router.get("/memory", status_code=status.HTTP_200_OK, response_model=ApiResponse[MemoryStats])
async def get_memory_stats() -> ApiResponse[MemoryStats]:
    """
    获取当前内存（RAM + Swap）状态数据。

    采集内容包括：
        - 物理内存：总量、可用、已用、使用率及多种细分指标（如 active、buffers 等）
        - 交换分区：总量、已用、空闲、使用率及换入换出累计量（平台支持时）

    Returns:
        ApiResponse[MemoryStats]: 统一响应外壳，data 字段包含 MemoryStats 模型。
    """
    stats = await collect_memory_stats(memory_stats_collector)
    return ApiResponse(data=stats)


@api_router.get("/disk", status_code=status.HTTP_200_OK, response_model=ApiResponse[DiskStats])
async def get_disk_stats() -> ApiResponse[DiskStats]:
    """
    获取磁盘状态数据（默认采集根目录 '/'）。

    采集内容包括：
        - 总容量、磁盘类型（SSD/HDD，若可识别）
        - 累计读写字节数、次数
        - 实时读写速率（字节/秒）及 IOPS
        - 利用率和平均响应时间（仅 Linux 有效）

    Returns:
        ApiResponse[DiskStats]: 统一响应外壳，data 字段包含 DiskStats 模型。
    """
    stats = await collect_disk_stats(
        disk_stats_collector,
        path="/",
        interval=MEASUREMENT_INTERVAL,
    )
    return ApiResponse(data=stats)


@api_router.get("/network", status_code=status.HTTP_200_OK, response_model=ApiResponse[NetworkStats])
async def get_network_stats() -> ApiResponse[NetworkStats]:
    """
    获取网络状态数据。

    采集内容包括：
        - 所有活跃（UP 且非回环）网卡名称
        - 各网卡配置：标称带宽、MTU、状态、IP 地址、MAC
        - 各网卡累计流量计数器（字节/包、错误/丢弃）
        - 各网卡实时收发速率（字节/秒）

    Returns:
        ApiResponse[NetworkStats]: 统一响应外壳，data 字段包含 NetworkStats 模型。
    """
    stats = await collect_network_stats(network_stats_collector, interval=MEASUREMENT_INTERVAL)
    return ApiResponse(data=stats)


@api_router.get("/gpu", status_code=status.HTTP_200_OK, response_model=ApiResponse[GPUStats])
async def get_gpu_stats() -> ApiResponse[GPUStats]:
    """
    获取 GPU 状态数据（仅当系统存在 NVIDIA GPU 且 nvidia-ml-py 可用时有效）。

    采集内容包括：
        - 每个 GPU 的名称、核心利用率、显存使用/总量、温度、功耗

    Returns:
        ApiResponse[GPUStats]: 统一响应外壳，data 字段包含 GPUStats 模型；
                                若无 GPU，则 gpus 列表为空。
    """
    stats = await collect_gpu_stats(gpu_stats_collector)
    return ApiResponse(data=stats)


# -------- 静态首页路由 --------

static_router = APIRouter(tags=["Static"])

# 挂载整个静态目录，提供 /static/* 访问
@static_router.get("/static/{full_path:path}")
async def serve_static(full_path: str):
    """
    返回前端文件。
    """
    # 尝试返回具体文件
    file_path = STATIC_DIR / full_path
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"detail": "File not exist"}


@static_router.get("/")
async def serve_index() -> FileResponse:
    """
    提供前端首页 HTML 文件。

    该路由对应 `GET /`，返回 `static/html/index.html` 文件。
    用于承载监控面板的前端界面。
    """
    return FileResponse(INDEX_PATH)
