import asyncio
import csv
import io
import os
import subprocess
import time
from typing import Dict, List, Union

import psutil  # 仅用于保持风格一致，实际未使用


class GPUStatsCollector:
    """
    异步 GPU 数据采集工具类。

    支持 NVIDIA（nvidia-smi）、AMD（rocm-smi）和 Intel（仅检测存在性）显卡。
    所有显存容量以 **字节（bytes）** 为单位。
    阻塞型操作通过线程池执行，不阻塞事件循环。

    使用示例：
        stats = GPUStats()
        gpus = await stats.get_gpu_metrics()
    """

    # ------------------------------------------------------------------
    # 内部辅助方法（线程池执行器）
    # ------------------------------------------------------------------

    async def _run_in_executor(self, func, *args, **kwargs):
        """在默认线程池中执行阻塞型同步函数。"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    # ------------------------------------------------------------------
    # 静态辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_float(value, default=0.0) -> float:
        """安全地将字符串转换为浮点数，失败返回默认值。"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    # ------------------------------------------------------------------
    # 各厂商同步采集方法（供线程池调用）
    # ------------------------------------------------------------------

    def _get_nvidia_metrics_sync(self) -> List[Dict[str, Union[str, float]]]:
        """
        通过 nvidia-smi 采集 NVIDIA GPU 指标。
        返回列表，每个元素为指标字典，若失败返回空列表。
        """
        results = []
        try:
            proc = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
                    "--format=csv,noheader,nounits"
                ],
                capture_output=True, text=True, timeout=3
            )
            if proc.returncode == 0 and proc.stdout.strip():
                for line in proc.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 6:
                        mem_used_mib = self._safe_float(parts[2])
                        mem_total_mib = self._safe_float(parts[3])
                        results.append({
                            "name": parts[0] or "NVIDIA GPU",
                            "gpu_util": self._safe_float(parts[1]),
                            "mem_used_bytes": mem_used_mib * 1024 * 1024,   # MiB -> bytes
                            "mem_total_bytes": mem_total_mib * 1024 * 1024,
                            "temp_c": self._safe_float(parts[4]),
                            "power_w": self._safe_float(parts[5])
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        return results


    def _get_amd_metrics_sync(self) -> List[Dict[str, Union[str, float]]]:
        """
        通过 rocm-smi 采集 AMD GPU 指标。
        返回列表，若失败返回空列表。
        """
        results = []
        try:
            proc = subprocess.run(
                ["rocm-smi", "--csv", "--showuse", "--showmeminfo", "vram", "--showtemp", "--showpower"],
                capture_output=True, text=True, timeout=3
            )
            if proc.returncode == 0 and proc.stdout.strip():
                reader = csv.DictReader(io.StringIO(proc.stdout))
                for row in reader:
                    # 通过关键词匹配列名（不区分大小写）
                    def get_val(keywords, default="0"):
                        for col, val in row.items():
                            if any(kw in col.lower() for kw in keywords):
                                return val
                        return default

                    gpu_id = get_val(["gpu"], "0")
                    use = self._safe_float(get_val(["gpu use", "use %"]))
                    # rocm-smi 的输出显存单位可能是字节，原逻辑假设为字节，先转 GB 再转回字节
                    mem_used_gb = self._safe_float(get_val(["used memory", "vram used"])) / 1e9
                    mem_total_gb = self._safe_float(get_val(["total memory", "vram total"])) / 1e9
                    results.append({
                        "name": f"AMD GPU {gpu_id}",
                        "gpu_util": use,
                        "mem_used_bytes": mem_used_gb * (1024 ** 3),
                        "mem_total_bytes": mem_total_gb * (1024 ** 3),
                        "temp_c": self._safe_float(get_val(["edge", "temperature"])),
                        "power_w": self._safe_float(get_val(["power", "average graphics package power"]))
                    })
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
        return results


    def _get_intel_metrics_sync(self) -> List[Dict[str, Union[str, float]]]:
        """
        检测 Intel 显卡是否存在（通过 /sys/class/drm ），
        若存在则返回一个占位条目（无详细指标），否则返回空列表。
        """
        try:
            if os.path.exists("/sys/class/drm/card0/device/vendor"):
                with open("/sys/class/drm/card0/device/vendor", "r") as f:
                    vendor = f.read().strip()
                if vendor == "0x8086":
                    return [{
                        "name": "Intel GPU (仅检测到硬件，详细指标需扩展)",
                        "gpu_util": 0.0,
                        "mem_used_bytes": 0.0,
                        "mem_total_bytes": 0.0,
                        "temp_c": 0.0,
                        "power_w": 0.0
                    }]
        except Exception:
            pass
        return []


    def _get_gpu_metrics_sync(self) -> List[Dict[str, Union[str, float]]]:
        """
        同步采集所有 GPU 指标（组合方法）。
        依次尝试 NVIDIA → AMD → Intel，返回第一个成功的结果。
        若均失败，返回空列表。
        """
        # 优先尝试 NVIDIA
        nvidia_results = self._get_nvidia_metrics_sync()
        if nvidia_results:
            return nvidia_results

        # 其次尝试 AMD
        amd_results = self._get_amd_metrics_sync()
        if amd_results:
            return amd_results

        # 最后尝试 Intel（仅检测存在性）
        intel_results = self._get_intel_metrics_sync()
        if intel_results:
            return intel_results

        return []


    # ------------------------------------------------------------------
    # 公开异步方法
    # ------------------------------------------------------------------

    async def get_gpu_metrics(self) -> List[Dict[str, Union[str, float]]]:
        """
        异步获取所有 GPU 的实时监控指标。

        :return: GPU 指标列表，每个元素包含：
            - name (str): GPU 名称
            - gpu_util (float): 利用率（%）
            - mem_used_bytes (float): 已用显存（字节）
            - mem_total_bytes (float): 总显存（字节）
            - temp_c (float): 温度（℃）
            - power_w (float): 功耗（W）
            若未检测到 GPU，返回空列表。
        """
        return await self._run_in_executor(self._get_gpu_metrics_sync)


    async def get_all(self) -> Dict[str, List]:
        """
        一次性获取所有 GPU 指标，附带采样时间戳。

        :return: 包含以下键的字典：
            - gpus (List[Dict]): 同 `get_gpu_metrics()` 的返回值
        """
        gpus = await self.get_gpu_metrics()
        return {
            "gpus": gpus
        }
