from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any


class DummyQueue:
    """Minimal queue implementation, without the optional clear() method."""

    def __init__(self) -> None:
        self.q: list[Any] = []

    def push(self, obj: Any) -> None:
        self.q.append(obj)

    def pop(self) -> Any | None:
        return self.q.pop() if self.q else None

    def peek(self) -> Any | None:
        return self.q[-1] if self.q else None

    def close(self) -> None:
        pass

    def __len__(self) -> int:
        return len(self.q)


class QueuelibTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="queuelib-tests-")
        self.qpath: Path = self.tempfilename()
        self.qdir = self.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.qdir)
        shutil.rmtree(self.tmpdir)

    def tempfilename(self) -> Path:
        with tempfile.NamedTemporaryFile(dir=self.tmpdir) as nf:
            return Path(nf.name)

    def mkdtemp(self) -> str:
        return tempfile.mkdtemp(dir=self.tmpdir)


def track_closed(cls):
    """Wraps a queue class to track down if close() method was called"""

    class TrackingClosed(cls):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.closed = False

        def close(self):
            super().close()
            self.closed = True

    return TrackingClosed
