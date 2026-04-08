from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


class FileSystemObjectStore:
    """Stores blobs on the local filesystem."""

    def __init__(self, base_path: str = "uploads") -> None:
        self._base = Path(base_path)
        self._base.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, data: bytes) -> str:
        dest = self._base / key
        dest.write_bytes(data)
        return str(dest)

    def get(self, key: str) -> bytes | None:
        dest = self._base / key
        if dest.exists():
            return dest.read_bytes()
        return None


@dataclass
class LocalObjectStore:
    """In-memory object store for tests."""

    objects: dict[str, bytes] = field(default_factory=dict)

    def put(self, key: str, data: bytes) -> str:
        self.objects[key] = data
        return f"memory://{key}"

    def get(self, key: str) -> bytes | None:
        return self.objects.get(key)
