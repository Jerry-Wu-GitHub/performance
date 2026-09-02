import asyncio
import socket
import time
from typing import Dict, List, Optional, Union

import psutil


class NetworkStatsCollector:
    """
    异步网络数据采集工具类。

    封装 psutil 获取网卡配置、流量统计和实时速率。所有容量相关字段（累计流量、速率）
    均以**字节**为单位，实时速率为**字节/秒**。网卡标称带宽（speed）单位为 Mb/s。

    阻塞型操作（需要间隔采样的速率计算）通过线程池执行，不阻塞事件循环。
    瞬时操作直接同步调用。

    使用示例：
        stats = NetworkStats()
        info = await stats.get_all(interval=0.5)
        for nic, data in info['nics'].items():
            print(f"{nic}: 发送 {data['speed_send_bytes']} B/s")
    """

    # ------------------------------------------------------------------
    # 内部辅助方法（线程池执行器）
    # ------------------------------------------------------------------

    async def _run_in_executor(self, func, *args, **kwargs):
        """在默认线程池中执行阻塞型同步函数。"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))


    # ------------------------------------------------------------------
    # 私有同步方法（供线程池调用）
    # ------------------------------------------------------------------

    def _get_active_nics_sync(self) -> List[str]:
        """
        同步获取当前系统中处于 UP 状态且至少有一个非回环 IP 地址的有效网卡列表。
        """
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        active = []
        for iface, addr_list in addrs.items():
            # 检查是否 UP
            if iface not in stats or not stats[iface].isup:
                continue
            # 检查是否有有效的 IPv4 或 IPv6 地址（排除回环）
            has_valid = False
            for addr in addr_list:
                if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                    has_valid = True
                    break
                if addr.family == socket.AF_INET6 and addr.address != '::1':
                    has_valid = True
                    break
            if has_valid:
                active.append(iface)
        return active


    def _sync_network_speeds(self, interval: float, nics: List[str]) -> Dict[str, Dict[str, float]]:
        """
        同步计算指定网卡的实时收发速率（字节/秒）。
        内部会 sleep(interval) 进行两次采样。
        """
        io_start = psutil.net_io_counters(pernic=True)
        time.sleep(interval)
        io_end = psutil.net_io_counters(pernic=True)

        speeds = {}
        for nic in nics:
            if nic in io_start and nic in io_end:
                sent_diff = io_end[nic].bytes_sent - io_start[nic].bytes_sent
                recv_diff = io_end[nic].bytes_recv - io_start[nic].bytes_recv
                speeds[nic] = {
                    "send_speed_bytes": sent_diff / interval,   # 字节/秒
                    "recv_speed_bytes": recv_diff / interval,
                }
            else:
                speeds[nic] = {"send_speed_bytes": 0.0, "recv_speed_bytes": 0.0}
        return speeds


    # ------------------------------------------------------------------
    # 公开异步方法
    # ------------------------------------------------------------------

    async def get_active_nics(self) -> List[str]:
        """
        获取当前有效的网卡名称列表（UP 且含有非回环 IP）。

        :return: 网卡名称列表
        """
        return await self._run_in_executor(self._get_active_nics_sync)


    async def get_nic_info(self, nics: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        获取指定网卡（或所有有效网卡）的配置信息。

        包括：带宽（Mb/s）、MTU、IPv4/IPv6 地址列表、MAC 地址（若有）。

        :param nics: 要查询的网卡名称列表，若为 None 则自动获取所有有效网卡
        :return: 字典，键为网卡名，值为包含配置信息的字典。
        """
        if nics is None:
            nics = await self.get_active_nics()

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        result = {}
        for nic in nics:
            nic_info = {}
            # 带宽和 MTU
            if nic in stats:
                stat = stats[nic]
                nic_info["speed_mbps"] = stat.speed if stat.speed > 0 else None
                nic_info["mtu"] = stat.mtu
                nic_info["is_up"] = stat.isup
            else:
                nic_info["speed_mbps"] = None
                nic_info["mtu"] = None
                nic_info["is_up"] = False

            # 地址信息
            addresses = {"ipv4": [], "ipv6": [], "mac": None}
            if nic in addrs:
                for addr in addrs[nic]:
                    if addr.family == socket.AF_INET:
                        addresses["ipv4"].append(addr.address)
                    elif addr.family == socket.AF_INET6:
                        addresses["ipv6"].append(addr.address)
                    elif addr.family == psutil.AF_LINK:  # MAC 地址
                        addresses["mac"] = addr.address
            nic_info["addresses"] = addresses
            result[nic] = nic_info
        return result


    async def get_io_counters(self, pernic: bool = True) -> Union[Dict[str, Dict[str, int]], Dict[str, int]]:
        """
        获取网络 I/O 累计流量计数器（自系统启动以来）。

        :param pernic: 若为 True，返回每个网卡的单独计数器；若为 False，返回所有网卡的总和。
        :return: 若 pernic=True，字典 {网卡名: {"bytes_sent": int, "bytes_recv": int, ...}}，
                 否则返回全局累计值 {"bytes_sent": int, "bytes_recv": int, ...}
        """
        io = psutil.net_io_counters(pernic=pernic)
        if pernic:
            # 过滤仅返回有效网卡？此处返回所有，由调用者决定
            result = {}
            for nic, counters in io.items():
                result[nic] = {
                    "bytes_sent": counters.bytes_sent,
                    "bytes_recv": counters.bytes_recv,
                    "packets_sent": counters.packets_sent,
                    "packets_recv": counters.packets_recv,
                    "errin": counters.errin,
                    "errout": counters.errout,
                    "dropin": counters.dropin,
                    "dropout": counters.dropout,
                }
            return result
        else:
            return {
                "bytes_sent": io.bytes_sent,
                "bytes_recv": io.bytes_recv,
                "packets_sent": io.packets_sent,
                "packets_recv": io.packets_recv,
                "errin": io.errin,
                "errout": io.errout,
                "dropin": io.dropin,
                "dropout": io.dropout,
            }


    async def get_network_speeds(self, interval: float = 1.0, nics: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
        """
        获取指定网卡（或所有有效网卡）的实时收发速率（字节/秒）。

        该操作会阻塞 `interval` 秒进行两次采样，因此在线程池中执行。

        :param interval: 采样间隔（秒），默认 1.0
        :param nics: 要查询的网卡列表，若为 None 则使用所有有效网卡
        :return: 字典 {网卡名: {"send_speed_bytes": float, "recv_speed_bytes": float}}
        """
        if nics is None:
            nics = await self.get_active_nics()
        if not nics:
            return {}
        return await self._run_in_executor(self._sync_network_speeds, interval, nics)


    async def get_all(self, interval: float = 1.0) -> Dict[str, Union[Dict, float]]:
        """
        一次性获取所有网络信息（配置、累计流量、实时速率）。

        并行执行，提高效率。实时速率采样约耗时 `interval` 秒。

        :param interval: 采样间隔（秒），用于速率计算
        :return: 包含以下键的字典：
            - active_nics (List[str]): 有效网卡列表
            - nic_info (Dict): 各网卡配置信息（同 get_nic_info）
            - io_counters (Dict): 各网卡累计流量（同 get_io_counters(pernic=True)）
            - speeds (Dict): 实时速率（同 get_network_speeds）
        """
        # 并行获取基础信息（瞬时）和速率（阻塞）
        active_task = self.get_active_nics()
        counters_task = self.get_io_counters(pernic=True)
        # 先获取有效网卡列表，再并行获取配置和速率
        active_nics = await active_task
        info_task = self.get_nic_info(active_nics)
        speeds_task = self.get_network_speeds(interval, active_nics) if active_nics else asyncio.sleep(0, result={})

        nic_info, speeds = await asyncio.gather(info_task, speeds_task)
        counters = await counters_task  # 已在上面启动

        return {
            "active_nics": active_nics,
            "nic_info": nic_info,
            "io_counters": counters,
            "speeds": speeds,
        }
