"""
内存状态数据模型与采集函数（RAM + Swap）
"""

import asyncio
from typing import Dict, Optional

from pydantic import Field

from .base import BaseSchema                      # 同级 base 模块
from ..stats_collectors import MemoryStatsCollector  # 上级 stats_collector


class MemoryStats(BaseSchema):
    """
    内存状态数据模型，包含物理内存（虚拟内存）与交换分区（Swap）的全部指标。
    所有容量字段均以 **字节（bytes）** 为单位。
    """

    # ---------- 物理内存（虚拟内存） ----------
    total_bytes: int = Field(
        description="物理内存总容量（字节）",
        ge=0,
    )
    available_bytes: int = Field(
        description="当前可用的物理内存容量（字节），含可回收缓存",
        ge=0,
    )
    used_bytes: int = Field(
        description="当前已使用的物理内存容量（字节）",
        ge=0,
    )
    usage_percent: float = Field(
        description="物理内存使用率（百分比，0~100）",
        ge=0.0,
        le=100.0,
    )
    free_bytes: Optional[int] = Field(
        description="完全空闲的物理内存容量（字节），可能低于 available_bytes；平台不支持时为 None",
        ge=0,
        default=None,
    )
    active_bytes: Optional[int] = Field(
        description="活动内存容量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )
    inactive_bytes: Optional[int] = Field(
        description="非活动内存容量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )
    buffers_bytes: Optional[int] = Field(
        description="缓冲区内存容量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )
    cached_bytes: Optional[int] = Field(
        description="缓存内存容量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )
    shared_bytes: Optional[int] = Field(
        description="共享内存容量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )
    slab_bytes: Optional[int] = Field(
        description="Slab 内存容量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )

    # ---------- 交换分区（Swap） ----------
    swap_total_bytes: int = Field(
        description="交换分区总容量（字节）",
        ge=0,
    )
    swap_used_bytes: int = Field(
        description="交换分区已使用容量（字节）",
        ge=0,
    )
    swap_free_bytes: int = Field(
        description="交换分区空闲容量（字节）",
        ge=0,
    )
    swap_percent: float = Field(
        description="交换分区使用率（百分比，0~100）",
        ge=0.0,
        le=100.0,
    )
    swap_sin_bytes: Optional[int] = Field(
        description="从磁盘换入的累计数据量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )
    swap_sout_bytes: Optional[int] = Field(
        description="换出到磁盘的累计数据量（字节），部分平台支持；不支持时为 None",
        ge=0,
        default=None,
    )


async def collect_memory_stats(
    collector: MemoryStatsCollector,
) -> MemoryStats:
    """
    异步采集内存状态数据，组装为 MemoryStats 对象。

    并发调用收集器的 `get_virtual_memory()` 与 `get_swap()` 方法，
    确保高效获取完整信息。所有操作均为瞬时读取，不阻塞事件循环。

    :param collector: MemoryStatsCollector 实例。
    :return: 填充完整的 MemoryStats 对象。
    """
    virtual_task = collector.get_virtual_memory()
    swap_task = collector.get_swap()
    virtual, swap = await asyncio.gather(virtual_task, swap_task)

    # 解包虚拟内存
    return MemoryStats(
        total_bytes=virtual["total_bytes"],
        available_bytes=virtual["available_bytes"],
        used_bytes=virtual["used_bytes"],
        usage_percent=virtual["percent"],
        free_bytes=virtual.get("free_bytes"),
        active_bytes=virtual.get("active_bytes"),
        inactive_bytes=virtual.get("inactive_bytes"),
        buffers_bytes=virtual.get("buffers_bytes"),
        cached_bytes=virtual.get("cached_bytes"),
        shared_bytes=virtual.get("shared_bytes"),
        slab_bytes=virtual.get("slab_bytes"),
        swap_total_bytes=swap["total_bytes"],
        swap_used_bytes=swap["used_bytes"],
        swap_free_bytes=swap["free_bytes"],
        swap_percent=swap["percent"],
        swap_sin_bytes=swap.get("sin_bytes"),
        swap_sout_bytes=swap.get("sout_bytes"),
    )
