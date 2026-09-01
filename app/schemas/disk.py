"""
磁盘状态数据模型与采集函数
"""

import asyncio
from typing import Optional

from pydantic import Field

from .base import BaseSchema                      # 同级 base 模块
from ..stats_collectors import DiskStatsCollector  # 上级 stats_collector


class DiskStats(BaseSchema):
    """
    磁盘状态数据模型，包含容量、类型、I/O 计数器、速率、IOPS、利用率和响应时间。
    所有容量与速率字段均以 **字节（bytes）** 为单位。
    """

    # ---------- 基础信息 ----------
    total_bytes: int = Field(
        description="磁盘总容量（字节）",
        ge=0,
    )
    disk_type: Optional[str] = Field(
        description="磁盘类型：'SSD' 或 'HDD'，若无法判断则为 None",
        default=None,
    )

    # ---------- I/O 计数器（累积值） ----------
    read_bytes: Optional[int] = Field(
        description="自系统启动以来的累计读取字节数，若无法获取则为 None",
        ge=0,
        default=None,
    )
    write_bytes: Optional[int] = Field(
        description="自系统启动以来的累计写入字节数，若无法获取则为 None",
        ge=0,
        default=None,
    )
    read_count: Optional[int] = Field(
        description="自系统启动以来的累计读取次数，若无法获取则为 None",
        ge=0,
        default=None,
    )
    write_count: Optional[int] = Field(
        description="自系统启动以来的累计写入次数，若无法获取则为 None",
        ge=0,
        default=None,
    )

    # ---------- 实时速率（字节/秒）与 IOPS ----------
    read_speed_bytes: float = Field(
        description="当前读取速率（字节/秒）",
        ge=0.0,
    )
    write_speed_bytes: float = Field(
        description="当前写入速率（字节/秒）",
        ge=0.0,
    )
    iops_read: float = Field(
        description="当前读取 IOPS（次/秒）",
        ge=0.0,
    )
    iops_write: float = Field(
        description="当前写入 IOPS（次/秒）",
        ge=0.0,
    )

    # ---------- 利用率和响应时间（来自 iostat） ----------
    utilization: float = Field(
        description="磁盘利用率（百分比，0~100），仅 Linux 有效，否则为 0.0",
        ge=0.0,
        le=100.0,
    )
    await_ms: float = Field(
        description="平均响应时间（毫秒），仅 Linux 有效，否则为 0.0",
        ge=0.0,
    )

    # ---------- 采样时间戳 ----------
    timestamp: float = Field(
        description="数据采集时间戳（Unix 秒数）",
        ge=0,
    )


async def collect_disk_stats(
    collector: DiskStatsCollector,
    path: str = "/",
    interval: float = 1.0,
) -> DiskStats:
    """
    异步采集磁盘状态数据，组装为 DiskStats 对象。

    该函数调用收集器的 `get_all` 方法，并发执行容量、类型、计数器、
    速率和 iostat 查询，总耗时约为 `interval` 秒（由速率和 iostat 采样决定）。

    :param collector: DiskStatsCollector 实例。
    :param path: 挂载点路径，用于获取总容量，默认为根目录 '/'。
    :param interval: 采样间隔（秒），用于速率和 iostat，默认 1.0 秒。
    :return: 填充完整的 DiskStats 对象。
    """
    # 一次获取所有数据（返回嵌套字典）
    data = await collector.get_all(path=path, interval=interval)

    # 展开各字段
    io_counters = data["io_counters"]
    io_rates = data["io_rates"]
    iostat = data["iostat"]

    return DiskStats(
        total_bytes=data["total_bytes"],
        disk_type=data.get("disk_type"),  # 可能为 None
        read_bytes=io_counters.get("read_bytes"),
        write_bytes=io_counters.get("write_bytes"),
        read_count=io_counters.get("read_count"),
        write_count=io_counters.get("write_count"),
        read_speed_bytes=io_rates["read_speed_bytes"],
        write_speed_bytes=io_rates["write_speed_bytes"],
        iops_read=io_rates["iops_read"],
        iops_write=io_rates["iops_write"],
        utilization=iostat["utilization"],
        await_ms=iostat["await_ms"],
        timestamp=data["timestamp"],
    )
