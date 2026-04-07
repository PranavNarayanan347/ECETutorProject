from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LocalObjectStore:
    objects: dict[str, bytes] = field(default_factory=dict)

    def put(self, key: str, data: bytes) -> str:
        self.objects[key] = data
        return f"memory://{key}"

    def get(self, key: str) -> bytes | None:
        return self.objects.get(key)
