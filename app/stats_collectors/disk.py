import asyncio
import re
import subprocess
import time
from typing import Dict, Optional, Union

import psutil


class DiskStatsCollector:
    """
    异步磁盘（存储）数据采集工具类（所有容量均以字节为单位）。

    封装 psutil 及系统命令（如 iostat）获取磁盘容量、类型、I/O 统计、
    读写速率（字节/秒）、IOPS、利用率和响应时间等指标。
    所有容量字段（总容量、读写字节数、速率）均使用**字节**作为单位。

    阻塞型操作（需等待采样间隔）通过线程池执行，不阻塞事件循环。
    瞬时操作直接同步调用，无额外开销。

    注意：部分功能（磁盘类型、iostat）依赖 Linux 特有接口，非 Linux 平台可能返回 None 或默认值。

    使用示例：
        stats = DiskStats()
        info = await stats.get_all()
        print(f"总容量: {info['total_bytes'] / (1024**3):.2f} GB")
        print(f"读取速率: {info['read_speed_bytes'] / (1024**2):.2f} MB/s")
    """

    # ------------------------------------------------------------------
    # 内部辅助方法（线程池执行器）
    # ------------------------------------------------------------------

    async def _run_in_executor(self, func, *args, **kwargs):
        """在默认线程池中执行阻塞型同步函数。"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


    # ------------------------------------------------------------------
    # 私有同步方法（供线程池调用，不包含异步操作）
    # ------------------------------------------------------------------

    def _get_root_device_sync(self) -> Optional[str]:
        """
        同步获取根目录对应的磁盘设备名（如 'sda'）。
        仅 Linux，通过 df 和 awk 提取。
        """
        try:
            output = subprocess.check_output(
                "df -h / | tail -1 | awk '{print $1}'",
                shell=True, text=True
            )
            device = output.strip()
            if device.startswith('/dev/'):
                device = device[5:]  # 去掉 '/dev/'
            # 去掉分区号（如 sda1 -> sda）
            device = re.sub(r'\d+$', '', device)
            return device if device else None
        except Exception:
            return None


    def _sync_io_rates(self, interval: float) -> Dict[str, float]:
        """
        同步计算磁盘读写速率（字节/秒）和 IOPS。
        内部会 sleep(interval) 进行两次采样。
        """
        io1 = psutil.disk_io_counters()
        if io1 is None:
            return {"read_speed_bytes": 0.0, "write_speed_bytes": 0.0,
                    "iops_read": 0.0, "iops_write": 0.0}
        time.sleep(interval)
        io2 = psutil.disk_io_counters()
        if io2 is None:
            return {"read_speed_bytes": 0.0, "write_speed_bytes": 0.0,
                    "iops_read": 0.0, "iops_write": 0.0}
        read_bytes_diff = io2.read_bytes - io1.read_bytes
        write_bytes_diff = io2.write_bytes - io1.write_bytes
        read_count_diff = io2.read_count - io1.read_count
        write_count_diff = io2.write_count - io1.write_count
        return {
            "read_speed_bytes": read_bytes_diff / interval,
            "write_speed_bytes": write_bytes_diff / interval,
            "iops_read": read_count_diff / interval,
            "iops_write": write_count_diff / interval,
        }


    def _sync_iostat(self, device: str, interval: float) -> Dict[str, float]:
        """
        同步执行 iostat -x 并解析利用率和响应时间（仅 Linux）。
        """
        try:
            cmd = f"iostat -x {interval} 2 | tail -n +4 | grep -E '^{device}|{device} ' | head -1"
            output = subprocess.check_output(cmd, shell=True, text=True)
            parts = output.split()
            if len(parts) >= 14:
                util = float(parts[-1])        # %util
                await_val = float(parts[-4])   # await (ms)
                return {"utilization": util, "await_ms": await_val}
            return {"utilization": 0.0, "await_ms": 0.0}
        except Exception:
            return {"utilization": 0.0, "await_ms": 0.0}


    # ------------------------------------------------------------------
    # 基础指标（瞬时操作）
    # ------------------------------------------------------------------

    async def get_total_bytes(self, path: str = '/') -> int:
        """
        获取指定挂载点的磁盘总容量（单位：字节）。

        :param path: 挂载点路径，默认为根目录 '/'
        :return: 总容量（字节）
        """
        usage = psutil.disk_usage(path)
        return usage.total


    async def get_disk_type(self, device_name: Optional[str] = None) -> Optional[str]:
        """
        获取磁盘类型（SSD / HDD）。

        通过读取 `/sys/block/<device>/queue/rotational` 判断：
        - 0 => SSD
        - 1 => HDD
        仅支持 Linux。若无法获取或非 Linux，返回 None。

        :param device_name: 设备名（如 'sda'），若为 None 则尝试自动获取根设备
        :return: 'SSD' 或 'HDD'，若无法判断则返回 None
        """
        if device_name is None:
            device_name = await self._get_root_device()
        if not device_name:
            return None
        try:
            with open(f"/sys/block/{device_name}/queue/rotational", 'r') as f:
                rotational = int(f.read().strip())
                return "HDD" if rotational == 1 else "SSD"
        except Exception:
            return None


    async def _get_root_device(self) -> Optional[str]:
        """
        异步获取根设备名（委托给线程池执行同步方法）。
        """
        return await self._run_in_executor(self._get_root_device_sync)


    # ------------------------------------------------------------------
    # 实时指标（瞬时读取累积值）
    # ------------------------------------------------------------------

    async def get_io_counters(self) -> Dict[str, Union[int, None]]:
        """
        获取磁盘 I/O 计数器累积值（自系统启动以来）。

        返回读取/写入的字节数和次数，所有容量均以字节为单位。

        :return: 包含以下键的字典：
            - read_bytes (int | None): 累计读取字节数
            - write_bytes (int | None): 累计写入字节数
            - read_count (int | None): 累计读取次数
            - write_count (int | None): 累计写入次数
        """
        io = psutil.disk_io_counters()
        if io is None:
            return {
                "read_bytes": None,
                "write_bytes": None,
                "read_count": None,
                "write_count": None,
            }
        return {
            "read_bytes": io.read_bytes,
            "write_bytes": io.write_bytes,
            "read_count": io.read_count,
            "write_count": io.write_count,
        }


    # ------------------------------------------------------------------
    # 实时速率（需采样间隔，阻塞操作）—— 速率单位为 字节/秒
    # ------------------------------------------------------------------

    async def get_io_rates(self, interval: float = 1.0) -> Dict[str, float]:
        """
        获取当前磁盘读写速率（字节/秒）和 IOPS（次/秒）。

        通过两次采样 `disk_io_counters()` 并计算差值除以间隔时间得到。
        该操作会阻塞 `interval` 秒（默认 1 秒），因此在线程池中执行。

        :param interval: 采样间隔（秒），必须为正数，默认 1.0
        :return: 包含以下键的字典：
            - read_speed_bytes (float): 读取速率（字节/秒）
            - write_speed_bytes (float): 写入速率（字节/秒）
            - iops_read (float): 读取 IOPS（次/秒）
            - iops_write (float): 写入 IOPS（次/秒）
            若无法获取计数器，所有值为 0.0
        """
        return await self._run_in_executor(self._sync_io_rates, interval)


    # ------------------------------------------------------------------
    # 利用率和响应时间（依赖 iostat，阻塞操作）
    # ------------------------------------------------------------------

    async def get_iostat(self, device: Optional[str] = None, interval: float = 1.0) -> Dict[str, float]:
        """
        通过 `iostat -x` 获取磁盘利用率和平均响应时间（仅 Linux）。

        该命令会采样两次，默认间隔 1 秒，因此阻塞约 `interval` 秒。
        若 `iostat` 不可用或解析失败，返回默认值 0.0。

        :param device: 指定设备名（如 'sda'），若为 None 则自动获取根设备
        :param interval: iostat 采样间隔（秒），默认 1.0
        :return: 包含以下键的字典：
            - utilization (float): 磁盘利用率（百分比，如 45.5）
            - await_ms (float): 平均响应时间（毫秒）
        """
        if device is None:
            device = await self._get_root_device()
        if not device:
            return {"utilization": 0.0, "await_ms": 0.0}
        return await self._run_in_executor(self._sync_iostat, device, interval)


    # ------------------------------------------------------------------
    # 组合方法
    # ------------------------------------------------------------------

    async def get_all(self, path: str = '/', interval: float = 1.0) -> Dict[str, Union[Dict, float]]:
        """
        一次性获取所有磁盘信息（基础 + 实时速率 + iostat）。

        该方法并行执行多项查询，提高效率。
        注意：由于 `get_io_rates` 和 `get_iostat` 都会阻塞约 `interval` 秒，
        实际总耗时约为 `interval`（并行执行）。

        :param path: 挂载点路径，用于获取容量
        :param interval: 采样间隔（秒），用于速率和 iostat
        :return: 包含以下键的字典：
            - total_bytes (int): 总容量（字节）
            - disk_type (str | None): SSD/HDD，或 None
            - io_counters (Dict): 累积 I/O 计数器（见 `get_io_counters`）
            - io_rates (Dict): 读写速率（字节/秒）和 IOPS（见 `get_io_rates`）
            - iostat (Dict): 利用率和 await（见 `get_iostat`）
            - timestamp (float): 采样时间戳
        """
        total_task = self.get_total_bytes(path)
        type_task = self.get_disk_type()
        counters_task = self.get_io_counters()
        rates_task = self.get_io_rates(interval)
        iostat_task = self.get_iostat(interval=interval)

        total, disk_type, counters, rates, iostat = await asyncio.gather(
            total_task, type_task, counters_task, rates_task, iostat_task
        )

        return {
            "total_bytes": total,
            "disk_type": disk_type,
            "io_counters": counters,
            "io_rates": rates,
            "iostat": iostat,
            "timestamp": time.time(),
        }
