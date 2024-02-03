from __future__ import annotations

import uuid
from typing import Callable, Optional

from pympler import asizeof

from utils.tuple import Tuple


class DebugTuple:
    def __init__(self, t: Tuple):
        self.uuid = str(uuid.uuid4().hex)

        self._tuple = t

        self._data = {}  # Extra data that also needs to be stored

        self._tupleMemorySize = self._tuple.calcMemorySize()  # Will not change anymore since tuple is cloned
        self._memorySize = 0  # Calculated

        self._onSizeChangeCallback: Optional[Callable] = None

        self._updateMemorySize()

        self._loaded = True  # Can be unloaded when moved to storage or memory cleared

    def getTuple(self) -> Tuple:
        return self._tuple

    def getData(self) -> dict:
        return self._data

    def registerAttribute(self, name: str, attr) -> DebugTuple:
        if self._data is None:  # Data was deleted
            return self

        self._data[name] = attr

        self._updateMemorySize()

        return self

    def getAttribute(self, name: str):
        return self._data.get(name)

    def registerMemoryChangeCallback(self, cb: Callable):
        self._onSizeChangeCallback = cb

    def getMemorySize(self) -> int:
        return self._memorySize

    def isLoaded(self) -> bool:
        return self._loaded

    def load(self, tupleData: Optional[tuple], data: dict):
        self._tuple.data = tupleData
        self._data = data

        self._loaded = True

    def unload(self):
        self._data = None
        self._tuple.data = None

        self._loaded = False

    def delete(self):
        self.unload()

        self._tuple = None

    def _updateMemorySize(self):
        old = self._memorySize

        ts = self._tupleMemorySize

        if self._data is not None:
            ts += asizeof.asizeof(self._data)

        self._memorySize = ts

        if self._onSizeChangeCallback is not None:
            self._onSizeChangeCallback(self, ts - old)  # Send difference
