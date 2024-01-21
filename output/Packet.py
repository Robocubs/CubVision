from typing import Any
from wpimath.geometry import Transform3d
import struct
    
class Packet:
    def __init__(self):
        self._data: list[int] = []

    def getData(self) -> list[int]:
        return self._data

    def getSize(self) -> int:
        return len(self._data)

    def _encodeGeneric(self, packFormat: str, *value: Any) -> None:
        self._data.extend(struct.pack(packFormat, *value))

    def encode8(self, value: int) -> None:
        self._encodeGeneric('>b', value)
        return self

    def encode32(self, value: int) -> None:
        self._encodeGeneric('>l', value)
        return self

    def encodeDouble(self, value: float) -> None:
        self._encodeGeneric('>d', value)
        return self

    def encodeBoolean(self, value: bool) -> None:
        self.encode8(1 if value else 0)
        return self
    
    def encodeTransform(self, value: Transform3d) -> None:
        self.encodeDouble(value.X())
        self.encodeDouble(value.Y())
        self.encodeDouble(value.Z())

        quaternion = value.rotation().getQuaternion()
        self.encodeDouble(quaternion.W())
        self.encodeDouble(quaternion.X())
        self.encodeDouble(quaternion.Y())
        self.encodeDouble(quaternion.Z())

        return self
