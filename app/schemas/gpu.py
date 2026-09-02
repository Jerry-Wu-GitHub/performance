"""
GPU 状态数据模型与采集函数
"""

from typing import List

from pydantic import Field

from .base import BaseSchema                      # 同级 base 模块
from ..stats_collectors import GPUStatsCollector  # 上级 stats_collector


class GPUMetrics(BaseSchema):
    """单个 GPU 的实时监控指标"""

    name: str = Field(
        description="GPU 名称（如 'NVIDIA GeForce RTX 3080'）",
    )
    gpu_util: float = Field(
        description="GPU 核心利用率（百分比，0~100）",
        ge=0.0,
        le=100.0,
    )
    mem_used_bytes: float = Field(
        description="已使用显存容量（字节）",
        ge=0.0,
    )
    mem_total_bytes: float = Field(
        description="显存总容量（字节）",
        ge=0.0,
    )
    temp_c: float = Field(
        description="GPU 温度（摄氏度）",
        ge=0.0,
    )
    power_w: float = Field(
        description="GPU 实时功耗（瓦特）",
        ge=0.0,
    )


class GPUStats(BaseSchema):
    """
    GPU 状态数据模型，包含所有 GPU 的监控指标。
    """

    gpus: List[GPUMetrics] = Field(
        description="所有 GPU 的指标列表，若无 GPU 则为空列表",
    )


async def collect_gpu_stats(
    collector: GPUStatsCollector,
) -> GPUStats:
    """
    异步采集 GPU 状态数据，组装为 GPUStats 对象。

    调用收集器的 `get_all` 方法获取所有 GPU 指标，并转换为模型实例。

    :param collector: GPUStatsCollector 实例。
    :return: 填充完整的 GPUStats 对象。
    """
    data = await collector.get_all()
    gpus = [GPUMetrics(**gpu) for gpu in data["gpus"]]
    return GPUStats(gpus=gpus)
