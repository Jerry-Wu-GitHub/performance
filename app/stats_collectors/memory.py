import asyncio
import time
from typing import Dict, Optional, Union

import psutil


class MemoryStatsCollector:
    """
    异步内存（RAM + Swap）数据采集工具类（所有容量均以字节为单位）。

    该类封装了 psutil 中与内存相关的同步接口，转换为异步协程。
    所有操作均为瞬时读取（微秒级），不会阻塞事件循环，
    因此无需委托给线程池执行。

    所有容量返回值均为整数（字节数），使用 `int` 类型，
    可能值较大（如几十 GB 对应 64 位整数），Python 的 `int` 可安全表示。

    使用示例：
        stats = MemoryStats()
        mem_info = await stats.get_virtual_memory()
        print(f"总内存: {mem_info['total_bytes'] / (1024**3):.2f} GB")  # 如需 GB，可自行转换
    """

    # ------------------------------------------------------------------
    # 公开异步方法（瞬时操作直接同步调用）
    # ------------------------------------------------------------------

    async def get_total_bytes(self) -> int:
        """
        获取物理内存总容量（单位：字节）。

        :return: 总内存字节数
        """
        mem = psutil.virtual_memory()
        return mem.total


    async def get_used_bytes(self) -> int:
        """
        获取当前已使用的物理内存容量（单位：字节）。

        该值包括正在使用的内存和部分缓存，但不包括可回收的缓存。
        实际可用内存请参考 `get_available_bytes()`。

        :return: 已使用内存字节数
        """
        mem = psutil.virtual_memory()
        return mem.used


    async def get_available_bytes(self) -> int:
        """
        获取当前可用的物理内存容量（单位：字节）。

        可用内存 = 空闲内存 + 可回收的缓存/缓冲区。
        此值更接近用户实际可用的内存量。

        :return: 可用内存字节数
        """
        mem = psutil.virtual_memory()
        return mem.available


    async def get_usage_percent(self) -> float:
        """
        获取当前物理内存使用率（百分比，0~100）。

        :return: 使用率（%），浮点数
        """
        mem = psutil.virtual_memory()
        return mem.percent


    async def get_virtual_memory(self) -> Dict[str, Union[int, float, None]]:
        """
        获取物理内存的完整信息快照（一次性返回多个指标）。

        所有容量字段均以 **字节（bytes）** 为单位，以 `_bytes` 后缀标识。
        部分高级字段（如 active、buffers 等）在某些平台上可能不可用，此时值为 `None`。

        :return: 包含以下键的字典：
            - total_bytes (int): 总容量（字节）
            - available_bytes (int): 可用容量（字节）
            - used_bytes (int): 已使用容量（字节）
            - percent (float): 使用率（%）
            - free_bytes (int | None): 完全空闲容量（字节）（可能低于 available）
            - active_bytes (int | None): 活动内存（字节）（部分平台支持）
            - inactive_bytes (int | None): 非活动内存（字节）（部分平台支持）
            - buffers_bytes (int | None): 缓冲区内存（字节）（部分平台支持）
            - cached_bytes (int | None): 缓存内存（字节）（部分平台支持）
            - shared_bytes (int | None): 共享内存（字节）（部分平台支持）
            - slab_bytes (int | None): Slab 内存（字节）（部分平台支持）
        """
        mem = psutil.virtual_memory()
        return {
            "total_bytes": mem.total,
            "available_bytes": mem.available,
            "used_bytes": mem.used,
            "percent": mem.percent,
            "free_bytes": mem.free if mem.free is not None else None,
            "active_bytes": mem.active if hasattr(mem, 'active') and mem.active is not None else None,
            "inactive_bytes": mem.inactive if hasattr(mem, 'inactive') and mem.inactive is not None else None,
            "buffers_bytes": mem.buffers if hasattr(mem, 'buffers') and mem.buffers is not None else None,
            "cached_bytes": mem.cached if hasattr(mem, 'cached') and mem.cached is not None else None,
            "shared_bytes": mem.shared if hasattr(mem, 'shared') and mem.shared is not None else None,
            "slab_bytes": mem.slab if hasattr(mem, 'slab') and mem.slab is not None else None,
        }


    async def get_swap(self) -> Dict[str, Union[int, float, None]]:
        """
        获取交换分区（Swap）的完整信息，所有容量均以字节为单位。

        若系统未配置 Swap，则总容量为 0，其他容量值也为 0。
        换入/换出累计值（sin/sout）为自系统启动以来的总字节数。

        :return: 包含以下键的字典：
            - total_bytes (int): Swap 总容量（字节）
            - used_bytes (int): 已使用容量（字节）
            - free_bytes (int): 空闲容量（字节）
            - percent (float): 使用率（%）
            - sin_bytes (int | None): 从磁盘换入的累计数据量（字节）（部分平台支持）
            - sout_bytes (int | None): 换出到磁盘的累计数据量（字节）（部分平台支持）
        """
        swap = psutil.swap_memory()
        return {
            "total_bytes": swap.total,
            "used_bytes": swap.used,
            "free_bytes": swap.free,
            "percent": swap.percent,
            "sin_bytes": swap.sin if hasattr(swap, 'sin') else None,
            "sout_bytes": swap.sout if hasattr(swap, 'sout') else None,
        }


    async def get_all(self) -> Dict[str, Union[Dict, float]]:
        """
        一次性获取所有内存和 Swap 信息（组合方法）。

        该方法内部并行调用 `get_virtual_memory()` 和 `get_swap()`，
        并将结果组合到一个字典中，附带采样时间戳。

        :return: 包含以下键的字典：
            - virtual (Dict): 物理内存信息（同 `get_virtual_memory()` 返回值）
            - swap (Dict): Swap 信息（同 `get_swap()` 返回值）
            - timestamp (float): 采样时间戳（Unix 秒数）
        """
        virtual_task = self.get_virtual_memory()
        swap_task = self.get_swap()
        virtual, swap = await asyncio.gather(virtual_task, swap_task)
        return {
            "virtual": virtual,
            "swap": swap,
            "timestamp": time.time(),
        }

    # 注：内存访问速度属于硬件规格，无法通过软件采集，故不提供相关方法。
