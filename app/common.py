"""
实例化全局的数据采集器对象。
"""

from .stats_collectors import (
    CPUStatsCollector,
    MemoryStatsCollector,
    DiskStatsCollector,
    NetworkStatsCollector,
    GPUStatsCollector,
)

cpu_stats_collector     = CPUStatsCollector()
memory_stats_collector  = MemoryStatsCollector()
disk_stats_collector    = DiskStatsCollector()
network_stats_collector = NetworkStatsCollector()
gpu_stats_collector     = GPUStatsCollector()
