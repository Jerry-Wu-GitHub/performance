"""
实例化全局的数据采集器对象。
"""

from functools import lru_cache

from .config import Config
from .stats_collectors import (
    CPUStatsCollector,
    MemoryStatsCollector,
    DiskStatsCollector,
    NetworkStatsCollector,
    GPUStatsCollector,
)


@lru_cache(maxsize=1)
def get_config() -> Config:
    """
    获取全局唯一的 Config 单例对象。
    """
    return Config()


@lru_cache(maxsize=1)
def get_cpu_stats_collector() -> CPUStatsCollector:
    """
    获取全局唯一的 CPUStatsCollector 单例对象。
    """
    return CPUStatsCollector()

@lru_cache(maxsize=1)
def get_memory_stats_collector() -> MemoryStatsCollector:
    """
    获取全局唯一的 MemoryStatsCollector 单例对象。
    """
    return MemoryStatsCollector()

@lru_cache(maxsize=1)
def get_disk_stats_collector() -> DiskStatsCollector:
    """
    获取全局唯一的 DiskStatsCollector 单例对象。
    """
    return DiskStatsCollector()

@lru_cache(maxsize=1)
def get_network_stats_collector() -> NetworkStatsCollector:
    """
    获取全局唯一的 NetworkStatsCollector 单例对象。
    """
    return NetworkStatsCollector()

@lru_cache(maxsize=1)
def get_gpu_stats_collector() -> GPUStatsCollector:
    """
    获取全局唯一的 GPUStatsCollector 单例对象。
    """
    return GPUStatsCollector()
