"""
网络状态数据模型与采集函数
"""

from typing import Dict, List, Optional

from pydantic import Field

from .base import BaseSchema                      # 同级 base 模块
from ..stats_collectors import NetworkStatsCollector  # 上级 stats_collector


class NicConfig(BaseSchema):
    """单个网卡的配置信息"""

    speed_mbps: Optional[int] = Field(
        description="网卡标称带宽（Mb/s），若无法获取则为 None",
        ge=0,
        default=None,
    )
    mtu: Optional[int] = Field(
        description="网卡 MTU 值，若无法获取则为 None",
        ge=0,
        default=None,
    )
    is_up: bool = Field(
        description="网卡是否处于 UP 状态",
    )
    ipv4: List[str] = Field(
        description="IPv4 地址列表",
        default_factory=list,
    )
    ipv6: List[str] = Field(
        description="IPv6 地址列表",
        default_factory=list,
    )
    mac: Optional[str] = Field(
        description="MAC 地址，若无则为 None",
        default=None,
    )


class NicCounters(BaseSchema):
    """单个网卡的累计流量计数器（自系统启动以来）"""

    bytes_sent: int = Field(
        description="累计发送字节数",
        ge=0,
    )
    bytes_recv: int = Field(
        description="累计接收字节数",
        ge=0,
    )
    packets_sent: int = Field(
        description="累计发送数据包数",
        ge=0,
    )
    packets_recv: int = Field(
        description="累计接收数据包数",
        ge=0,
    )
    errin: int = Field(
        description="接收错误数",
        ge=0,
    )
    errout: int = Field(
        description="发送错误数",
        ge=0,
    )
    dropin: int = Field(
        description="接收丢弃包数",
        ge=0,
    )
    dropout: int = Field(
        description="发送丢弃包数",
        ge=0,
    )


class NicSpeeds(BaseSchema):
    """单个网卡的实时收发速率"""

    send_speed_bytes: float = Field(
        description="发送速率（字节/秒）",
        ge=0.0,
    )
    recv_speed_bytes: float = Field(
        description="接收速率（字节/秒）",
        ge=0.0,
    )


class NetworkStats(BaseSchema):
    """
    网络状态数据模型，包含所有有效网卡的配置、累计计数器和实时速率。
    """

    active_nics: List[str] = Field(
        description="当前系统中处于 UP 且拥有非回环 IP 的网卡名称列表",
        min_length=0,
    )
    nic_configs: Dict[str, NicConfig] = Field(
        description="各网卡的配置信息，键为网卡名",
    )
    nic_counters: Dict[str, NicCounters] = Field(
        description="各网卡的累计流量计数器，键为网卡名",
    )
    nic_speeds: Dict[str, NicSpeeds] = Field(
        description="各网卡的实时收发速率（字节/秒），键为网卡名",
    )
    timestamp: float = Field(
        description="数据采集时间戳（Unix 秒数）",
        ge=0,
    )


async def collect_network_stats(
    collector: NetworkStatsCollector,
    interval: float = 1.0,
) -> NetworkStats:
    """
    异步采集网络状态数据，组装为 NetworkStats 对象。

    调用收集器的 `get_all` 方法，一次性获取所有网卡的配置、计数器和速率，
    并发执行提高效率，总耗时约为 `interval` 秒（由速率采样决定）。

    :param collector: NetworkStatsCollector 实例。
    :param interval: 采样间隔（秒），用于实时速率计算，默认 1.0 秒。
    :return: 填充完整的 NetworkStats 对象。
    """
    data = await collector.get_all(interval=interval)

    # 构造嵌套字典，将原始数据转换为模型实例
    nic_configs = {}
    nic_counters = {}
    nic_speeds = {}

    for nic in data["active_nics"]:
        # 配置信息
        cfg = data["nic_info"].get(nic, {})
        addresses = cfg.get("addresses", {})
        nic_configs[nic] = NicConfig(
            speed_mbps=cfg.get("speed_mbps"),
            mtu=cfg.get("mtu"),
            is_up=cfg.get("is_up", False),
            ipv4=addresses.get("ipv4", []),
            ipv6=addresses.get("ipv6", []),
            mac=addresses.get("mac"),
        )

        # 累计计数器
        cnt = data["io_counters"].get(nic, {})
        nic_counters[nic] = NicCounters(
            bytes_sent=cnt.get("bytes_sent", 0),
            bytes_recv=cnt.get("bytes_recv", 0),
            packets_sent=cnt.get("packets_sent", 0),
            packets_recv=cnt.get("packets_recv", 0),
            errin=cnt.get("errin", 0),
            errout=cnt.get("errout", 0),
            dropin=cnt.get("dropin", 0),
            dropout=cnt.get("dropout", 0),
        )

        # 实时速率
        spd = data["speeds"].get(nic, {})
        nic_speeds[nic] = NicSpeeds(
            send_speed_bytes=spd.get("send_speed_bytes", 0.0),
            recv_speed_bytes=spd.get("recv_speed_bytes", 0.0),
        )

    return NetworkStats(
        active_nics=data["active_nics"],
        nic_configs=nic_configs,
        nic_counters=nic_counters,
        nic_speeds=nic_speeds,
        timestamp=data["timestamp"],
    )
