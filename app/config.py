"""
配置
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Callable, Optional, TypeVar

from dotenv import load_dotenv

from .constants import (
    DEFAULT_BASE_DIR,
    DEFAULT_STATIC_DIR,
    DEFAULT_INDEX_PATH,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_PERFORMANCE_MEASUREMENT_INTERVAL,
)


load_dotenv()


EnvValue = TypeVar("EnvValue")

def getenv(
    name: str,
    default: EnvValue,
    convert: Optional[Callable[[str], EnvValue]] = None,
    *,
    ignore_exception: bool = True
) -> EnvValue:
    """
    读取并转换环境变量为指定类型。

    Args:
        name: 环境变量名。
        default: 当环境变量值为 None、空字符串，或者转换失败且 ignore_exception=True 时返回。
        convert: 将非空字符串转换为目标类型的可调用对象。
        ignore_exception: 如果为 True，则在 convert 转换失败时返回 default。
    """
    value: Optional[str] = os.getenv(name)

    # 值为 None 或 空
    if not value:
        return default

    if convert:
        # 提供了转换器，尝试转换
        try:
            return convert(value)
        except Exception as exp:
            # 转换失败
            if ignore_exception:
                return default
            raise exp

    return value



# ==== 读取环境变量 ====

_BASE_DIR: Path = getenv("BASE_DIR", DEFAULT_BASE_DIR, Path)
_STATIC_DIR: Path = getenv("STATIC_DIR", DEFAULT_STATIC_DIR, Path)
_INDEX_PATH: Path = getenv("INDEX_PATH", DEFAULT_INDEX_PATH, Path)

_HOST: str = getenv("HOST", DEFAULT_HOST)
_PORT: int = getenv("PORT", DEFAULT_PORT, int)

_PERFORMANCE_MEASUREMENT_INTERVAL: float = getenv(
    "PERFORMANCE_MEASUREMENT_INTERVAL",
    DEFAULT_PERFORMANCE_MEASUREMENT_INTERVAL,
    float
)


@dataclass
class Config:
    """项目全局配置。

    所有字段的默认值来自环境变量，环境变量未设置时回退到
    :mod:`app.constants` 中定义的常量。

    请通过 :func:`get_config` 获取全局唯一实例。
    """

    base_dir: Path = field(
        default=_BASE_DIR,
        metadata={"description": "项目根目录"}
    )

    static_dir: Path = field(
        default=_STATIC_DIR,
        metadata={"description": "静态资源目录"}
    )

    index_path: Path = field(
        default=_INDEX_PATH,
        metadata={"description": "index目录"}
    )

    host: str = field(
        default=_HOST,
        metadata={"description": "运行时主机名"}
    )

    port: int = field(
        default=_PORT,
        metadata={"description": "运行时端口"}
    )

    performance_measurement_interval: float = field(
        default=_PERFORMANCE_MEASUREMENT_INTERVAL,
        metadata={"description": "终端初始时的工作目录"}
    )
