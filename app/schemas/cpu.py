"""
CPU 状态数据模型与采集函数
"""

import asyncio
from typing import List, Optional

from pydantic import Field

from .base import BaseSchema                # 同级目录下的 base 模块
from ..stats_collectors import CPUStatsCollector  # 上级目录的 stats_collector 模块


class CPUStats(BaseSchema):
    """
    CPU 状态数据模型，用于承载一次采集所得的全部 CPU 相关指标。

    所有字段均包含 description，并尽可能通过 Field 约束取值范围。
    """

    # 基础硬件信息
    physical_cores: int = Field(
        description="物理 CPU 核心数（不含超线程）",
        gt=0,
    )
    logical_cores: int = Field(
        description="逻辑 CPU 核心数（含超线程）",
        gt=0,
    )
    current_freq_mhz: Optional[float] = Field(
        description="当前 CPU 实时运行频率（MHz），若平台不支持则为 None",
        ge=0,
        default=None,
    )
    max_freq_mhz: Optional[float] = Field(
        description="CPU 基准/最大运行频率（MHz），若平台不支持则为 None",
        ge=0,
        default=None,
    )

    # 使用率（采样获得）
    overall_usage: float = Field(
        description="整体 CPU 使用率（百分比，0~100）",
        ge=0.0,
        le=100.0,
    )
    per_cpu_usage: List[float] = Field(
        description="每个逻辑核心的使用率列表（百分比，0~100）",
        min_length=1,
    )

    # 系统负载（仅 Unix/Linux/macOS 可靠）
    load_avg_1min: Optional[float] = Field(
        description="1 分钟平均负载（运行队列长度），若无支持则为 None",
        ge=0,
        default=None,
    )
    load_avg_5min: Optional[float] = Field(
        description="5 分钟平均负载（运行队列长度），若无支持则为 None",
        ge=0,
        default=None,
    )
    load_avg_15min: Optional[float] = Field(
        description="15 分钟平均负载（运行队列长度），若无支持则为 None",
        ge=0,
        default=None,
    )

    # 进程数与运行时间
    process_count: int = Field(
        description="当前系统正在运行的进程总数",
        ge=0,
    )
    uptime_seconds: float = Field(
        description="系统自上次启动以来的运行秒数",
        ge=0,
    )

    # CPU 统计计数（累积值）
    ctx_switches: int = Field(
        description="自系统启动以来的上下文切换总数",
        ge=0,
    )
    interrupts: int = Field(
        description="自系统启动以来的硬件中断总数",
        ge=0,
    )
    soft_interrupts: int = Field(
        description="自系统启动以来的软件中断总数",
        ge=0,
    )


async def collect_cpu_stats(
    collector: CPUStatsCollector,
    interval: float = 1.0,
) -> CPUStats:
    """
    异步采集 CPU 状态数据，组装为 CPUStats 对象。

    该函数并发调用收集器的多个异步方法，在保证采集效率的同时，
    将阻塞型操作（如 `get_usage` 的采样等待）委托给线程池执行。

    :param collector: CPUStatsCollector 实例，负责底层数据获取。
    :param interval: CPU 使用率的采样间隔（秒），默认 1.0 秒。
                     该值会传递给 `collector.get_usage(interval)`。
    :return: 填充完整的 CPUStats 对象。
    :raises ValueError: 当 interval 为非正数时，由 collector.get_usage 抛出。
    """
    # 并发执行所有采集任务，减少总耗时
    (
        basic_info,
        usage_result,
        current_freq,
        loadavg_result,
        process_count,
        uptime_seconds,
        stats_result,
    ) = await asyncio.gather(
        collector.get_basic_info(),
        collector.get_usage(interval=interval),
        collector.get_current_freq(),
        collector.get_loadavg(),
        collector.get_process_count(),
        collector.get_uptime_hours(),
        collector.get_stats(),
    )

    # 解包基础信息
    physical_cores = basic_info["physical_cores"]
    logical_cores = basic_info["logical_cores"]
    max_freq_mhz = basic_info["max_freq_mhz"]

    # 解包使用率
    overall_usage = usage_result["overall"]
    per_cpu_usage = usage_result["per_cpu"]

    # 解包负载（可能为 None）
    load_avg_1min = loadavg_result.get("load1") if loadavg_result else None
    load_avg_5min = loadavg_result.get("load5") if loadavg_result else None
    load_avg_15min = loadavg_result.get("load15") if loadavg_result else None

    # 解包统计计数
    ctx_switches = stats_result["ctx_switches"]
    interrupts = stats_result["interrupts"]
    soft_interrupts = stats_result["soft_interrupts"]

    # 构造并返回模型实例
    return CPUStats(
        physical_cores=physical_cores,
        logical_cores=logical_cores,
        current_freq_mhz=current_freq,
        max_freq_mhz=max_freq_mhz,
        overall_usage=overall_usage,
        per_cpu_usage=per_cpu_usage,
        load_avg_1min=load_avg_1min,
        load_avg_5min=load_avg_5min,
        load_avg_15min=load_avg_15min,
        process_count=process_count,
        uptime_seconds=uptime_seconds,
        ctx_switches=ctx_switches,
        interrupts=interrupts,
        soft_interrupts=soft_interrupts,
    )
