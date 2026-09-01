import asyncio
import time
from functools import partial
from typing import Dict, List, Optional, Union

import psutil


class CPUStatsCollector:
    """
    异步 CPU 数据采集工具类。

    该类封装了 psutil 库中与 CPU 相关的同步接口，将其转换为异步协程，
    并保证阻塞型操作（如带采样间隔的 `cpu_percent`）不会阻塞事件循环。
    所有公开方法均为 `async`，可直接在 `asyncio` 环境中使用。

    使用示例：
        stats = CPUStats()
        basic = await stats.get_basic_info()
        usage = await stats.get_usage(interval=0.5)
    """

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    async def _run_in_executor(self, func, *args, **kwargs):
        """
        在默认线程池中执行阻塞型同步函数，确保不阻塞事件循环。

        该辅助方法仅用于真正会阻塞（耗时 ≥ 1ms）的操作，
        例如带有 `interval` 参数的 `cpu_percent` 调用。

        :param func: 要执行的同步函数
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 函数执行结果
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))


    # ------------------------------------------------------------------
    # 公开异步方法（瞬时操作直接同步调用）
    # ------------------------------------------------------------------

    async def get_basic_info(self) -> Dict[str, Union[int, float, None]]:
        """
        获取 CPU 基础硬件信息（瞬时返回，不阻塞）。

        包括物理核心数、逻辑核心数、当前运行频率及基准（最大）频率。
        所有数值均从系统缓存读取，耗时通常在微秒级别。

        :return: 包含以下键的字典：
            - physical_cores (int): 物理核心数
            - logical_cores (int): 逻辑核心数（含超线程）
            - current_freq_mhz (float | None): 当前频率（MHz），若无法获取则为 None
            - max_freq_mhz (float | None): 基准/最大频率（MHz），若无法获取则为 None
        """
        physical = psutil.cpu_count(logical=False)
        logical = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        return {
            "physical_cores": physical,
            "logical_cores": logical,
            "current_freq_mhz": round(freq.current) if freq else None,
            "max_freq_mhz": round(freq.max) if freq else None,
        }


    async def get_current_freq(self) -> Optional[float]:
        """
        获取当前 CPU 实时运行频率（单位 MHz）。

        该值是动态频率，可能随负载变化。若平台不支持频率读取，返回 None。
        操作瞬时完成，不阻塞事件循环。

        :return: 当前频率（MHz），若不可用则返回 None
        """
        freq = psutil.cpu_freq()
        return freq.current if freq else None


    async def get_process_count(self) -> int:
        """
        获取当前系统中正在运行的进程总数。

        该值通过 `psutil.pids()` 获取，瞬时返回。

        :return: 进程数量
        """
        return len(psutil.pids())


    async def get_boot_time(self) -> float:
        """
        获取系统的启动时间戳（单位：秒）。

        使用 `psutil.boot_time()` 获取启动时间戳。
        瞬时返回，不涉及阻塞操作。

        :return: 启动时间戳（单位：秒）
        """
        boot = psutil.boot_time()
        return boot


    async def get_uptime_hours(self) -> float:
        """
        获取系统自上次启动以来的运行时间，单位为秒。

        使用 `psutil.boot_time()` 获取启动时间戳，与当前时间比较。
        瞬时返回，不涉及阻塞操作。

        :return: 运行秒数（浮点数）
        """
        boot = await self.get_boot_time()
        return time.time() - boot


    async def get_stats(self) -> Dict[str, int]:
        """
        获取系统 CPU 统计信息（自启动以来的累积计数值）。

        这些指标反映系统内核活动，包括上下文切换、硬中断和软中断次数。
        常用于性能监控。瞬时返回。

        :return: 包含以下键的字典：
            - ctx_switches (int): 上下文切换总数
            - interrupts (int): 硬件中断总数
            - soft_interrupts (int): 软件中断总数
        """
        stats = psutil.cpu_stats()
        return {
            "ctx_switches": stats.ctx_switches,
            "interrupts": stats.interrupts,
            "soft_interrupts": stats.soft_interrupts,
        }


    async def get_loadavg(self) -> Optional[Dict[str, float]]:
        """
        获取系统平均负载（Load Average），即 1、5、15 分钟内的平均运行队列长度。

        该指标在 Unix/Linux/macOS 上原生支持；
        Windows 平台从 psutil 5.6.2 开始提供模拟值（但可能不够准确）。
        若当前系统不支持（如旧版 psutil 或非兼容平台），则返回 None。

        :return: 包含以下键的字典，若支持：
            - load1 (float): 1 分钟平均负载
            - load5 (float): 5 分钟平均负载
            - load15 (float): 15 分钟平均负载
            若不支持，返回 None
        """
        if not hasattr(psutil, "getloadavg"):
            return None
        load1, load5, load15 = psutil.getloadavg()
        return {"load1": load1, "load5": load5, "load15": load15}


    # ------------------------------------------------------------------
    # 阻塞型操作（需在线程池中执行）
    # ------------------------------------------------------------------

    async def get_usage(self, interval: float = 1.0) -> Dict[str, Union[float, List[float]]]:
        """
        获取 CPU 使用率（采样方式）。

        该方法会等待指定的 `interval` 秒，然后返回该时间段内的平均使用率。
        由于内部会主动睡眠，此操作会阻塞调用线程，因此被委托给线程池执行，
        以避免阻塞事件循环。

        该方法并行获取整体使用率和每个核心的使用率，两者同时采样，
        总耗时约等于 `interval`（加上少量线程调度开销）。

        :param interval: 采样间隔（秒），必须为正数。默认 1.0 秒。
                         建议值 ≥ 0.1，过小会导致结果不稳定。
        :return: 包含以下键的字典：
            - overall (float): 整体 CPU 使用率（百分比，0~100）
            - per_cpu (List[float]): 每个逻辑核心的使用率列表（百分比，0~100）
        :raises ValueError: 若 `interval` 为非正数（psutil 内部可能拒绝）
        """
        # 使用两个线程并行执行，因为两者都需要相同的等待时间
        overall_task = self._run_in_executor(psutil.cpu_percent, interval=interval, percpu=False)
        per_cpu_task = self._run_in_executor(psutil.cpu_percent, interval=interval, percpu=True)
        overall, per_cpu = await asyncio.gather(overall_task, per_cpu_task)
        return {"overall": overall, "per_cpu": per_cpu}
