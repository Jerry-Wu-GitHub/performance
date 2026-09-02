import asyncio
from re import Pattern
from typing import Any, Callable, Coroutine, Iterable, List, Optional, Sequence, Tuple

from starlette.requests import HTTPConnection


class DependenceMounter:
    """
    用于储存 FastAPI 依赖函数。
    """

    def __init__(
        self,
        dependences: Optional[Sequence[Tuple[Optional[Pattern], Callable]]] = None
    ):
        """
        Args:
            dependences:
                每个元素是：(用于匹配路由的模式, 要调用的依赖函数（异步函数）)
                若模式为 None，则全部匹配。
        """
        self.dependences: List[Tuple[Optional[Pattern], Callable]] = list(dependences) if dependences else []


    def register(
        self,
        dependence: Callable,
        route_pattern: Optional[Pattern] = None,
    ) -> None:
        """
        注册一个依赖函数。
        """
        self.dependences.append((route_pattern, dependence))


    def _match_dependences(self, url: str) -> Iterable[Coroutine]:
        """
        返回该路由要执行的依赖。
        """
        return (
            dependence()
            for route_pattern, dependence in self.dependences
            if (route_pattern is None) or route_pattern.fullmatch(url)
        )


    async def depend(
        self,
        connection: HTTPConnection
    ) -> List[Any]:
        """
        并发调用所有的依赖函数。
        """
        url = connection.url
        tasks = self._match_dependences(url)
        return await asyncio.gather(*tasks)
