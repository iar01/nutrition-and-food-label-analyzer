import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from labellens.api.errors import ApiError


class RunSlots:
    def __init__(self, slots: int) -> None:
        self._sem = asyncio.Semaphore(slots)

    async def acquire(self) -> None:
        if self._sem.locked():
            raise ApiError(
                503,
                "busy",
                "The server is busy, try again in a few seconds.",
                headers={"Retry-After": "5"},
            )
        await self._sem.acquire()

    def release(self) -> None:
        self._sem.release()

    @asynccontextmanager
    async def slot(self) -> AsyncIterator[None]:
        await self.acquire()
        try:
            yield
        finally:
            self.release()
