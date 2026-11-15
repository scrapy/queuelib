from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from queuelib import (
    FifoDiskQueue,
    FifoMemoryQueue,
    FifoSQLiteQueue,
    LifoDiskQueue,
    LifoMemoryQueue,
    LifoSQLiteQueue,
)
from queuelib.queue import BaseQueue

from . import DummyQueue

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from . import ClearableQueue


class TestInterface:
    def test_queue(self) -> None:
        queue = BaseQueue()  # type: ignore[abstract]
        with pytest.raises(NotImplementedError):
            queue.push(b"")
        with pytest.raises(NotImplementedError):
            queue.peek()
        with pytest.raises(NotImplementedError):
            queue.pop()
        with pytest.raises(NotImplementedError):
            len(queue)
        queue.close()

    def test_issubclass(self) -> None:
        assert not issubclass(list, BaseQueue)
        assert not issubclass(int, BaseQueue)
        assert issubclass(DummyQueue, BaseQueue)
        assert issubclass(FifoMemoryQueue, BaseQueue)
        assert issubclass(LifoMemoryQueue, BaseQueue)
        assert issubclass(FifoDiskQueue, BaseQueue)
        assert issubclass(LifoDiskQueue, BaseQueue)
        assert issubclass(FifoSQLiteQueue, BaseQueue)
        assert issubclass(LifoSQLiteQueue, BaseQueue)

    def test_isinstance(self, tmp_path: Path) -> None:
        assert not isinstance(1, BaseQueue)
        assert not isinstance([], BaseQueue)
        assert isinstance(DummyQueue(), BaseQueue)
        assert isinstance(FifoMemoryQueue(), BaseQueue)
        assert isinstance(LifoMemoryQueue(), BaseQueue)
        for cls in [FifoDiskQueue, LifoDiskQueue, FifoSQLiteQueue, LifoSQLiteQueue]:
            queue = cls(tmp_path / cls.__name__)
            assert isinstance(queue, BaseQueue)
            queue.close()


class QueueTestMixin:
    def test_empty(self, make_queue: Callable[[], ClearableQueue]) -> None:
        """Empty queue test"""
        q = make_queue()
        assert q.pop() is None
        q.close()

    def test_single_pushpop(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        q.push(b"a")
        assert q.pop() == b"a"
        q.close()

    def test_binary_element(self, make_queue: Callable[[], ClearableQueue]) -> None:
        elem = (
            b"\x80\x02}q\x01(U\x04bodyq\x02U\x00U\t_encodingq\x03U\x05utf-"
            b"8q\x04U\x07cookiesq\x05}q\x06U\x04metaq\x07}q\x08U\x07header"
            b"sq\t}U\x03urlq\nX\x15\x00\x00\x00file:///tmp/tmphDJYsgU\x0bd"
            b"ont_filterq\x0b\x89U\x08priorityq\x0cK\x00U\x08callbackq\rNU"
            b"\x06methodq\x0eU\x03GETq\x0fU\x07errbackq\x10Nu."
        )
        q = make_queue()
        q.push(elem)
        assert q.pop() == elem
        q.close()

    def test_len(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        assert len(q) == 0
        q.push(b"a")
        assert len(q) == 1
        q.push(b"b")
        q.push(b"c")
        assert len(q) == 3
        q.pop()
        q.pop()
        q.pop()
        assert len(q) == 0
        q.close()

    def test_clear(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        q.clear()
        assert len(q) == 0
        q.push(b"a")
        q.push(b"b")
        q.clear()
        assert len(q) == 0
        assert q.peek() is None
        assert q.pop() is None
        q.push(b"c")
        assert q.pop() == b"c"
        q.close()

    def test_peek_one_element(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        assert q.peek() is None
        q.push(b"a")
        assert q.peek() == b"a"
        assert q.pop() == b"a"
        assert q.peek() is None
        q.close()


class FifoTestMixin:
    def test_push_pop1(self, make_queue: Callable[[], ClearableQueue]) -> None:
        """Basic push/pop test"""
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        assert q.pop() == b"a"
        assert q.pop() == b"b"
        assert q.pop() == b"c"
        assert q.pop() is None
        q.close()

    def test_push_pop2(self, make_queue: Callable[[], ClearableQueue]) -> None:
        """Test interleaved push and pops"""
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        q.push(b"d")
        assert q.pop() == b"a"
        assert q.pop() == b"b"
        q.push(b"e")
        assert q.pop() == b"c"
        assert q.pop() == b"d"
        assert q.pop() == b"e"
        q.close()

    def test_peek_fifo(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        assert q.peek() is None
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        assert q.peek() == b"a"
        assert q.peek() == b"a"
        assert q.pop() == b"a"
        assert q.peek() == b"b"
        assert q.peek() == b"b"
        assert q.pop() == b"b"
        assert q.peek() == b"c"
        assert q.peek() == b"c"
        assert q.pop() == b"c"
        assert q.peek() is None
        q.close()

    def test_push_after_peek(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        assert q.peek() == b"a"
        q.push(b"c")
        assert q.pop() == b"a"
        assert q.pop() == b"b"
        assert q.pop() == b"c"
        assert q.pop() is None
        q.close()


class LifoTestMixin:
    def test_push_pop1(self, make_queue: Callable[[], ClearableQueue]) -> None:
        """Basic push/pop test"""
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        assert q.pop() == b"c"
        assert q.pop() == b"b"
        assert q.pop() == b"a"
        assert q.pop() is None
        q.close()

    def test_push_pop2(self, make_queue: Callable[[], ClearableQueue]) -> None:
        """Test interleaved push and pops"""
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        q.push(b"d")
        assert q.pop() == b"d"
        assert q.pop() == b"c"
        q.push(b"e")
        assert q.pop() == b"e"
        assert q.pop() == b"b"
        assert q.pop() == b"a"
        q.close()

    def test_peek_lifo(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        assert q.peek() is None
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        assert q.peek() == b"c"
        assert q.peek() == b"c"
        assert q.pop() == b"c"
        assert q.peek() == b"b"
        assert q.peek() == b"b"
        assert q.pop() == b"b"
        assert q.peek() == b"a"
        assert q.peek() == b"a"
        assert q.pop() == b"a"
        assert q.peek() is None
        q.close()

    def test_push_after_peek(self, make_queue: Callable[[], ClearableQueue]) -> None:
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        assert q.peek() == b"b"
        q.push(b"c")
        assert q.pop() == b"c"
        assert q.pop() == b"b"
        assert q.pop() == b"a"
        assert q.pop() is None
        q.close()


class PersistentTestMixin:
    chunksize = 100000

    def test_non_bytes_raises_typeerror(
        self, make_queue: Callable[[], ClearableQueue]
    ) -> None:
        q = make_queue()
        try:
            with pytest.raises(TypeError):
                q.push(0)
            with pytest.raises(TypeError):
                q.push("")
            with pytest.raises(TypeError):
                q.push(None)
            with pytest.raises(TypeError):
                q.push(lambda x: x)
        finally:
            q.close()

    def test_text_in_windows(self, make_queue: Callable[[], ClearableQueue]) -> None:
        e1 = b"\r\n"
        q = make_queue()
        q.push(e1)
        q.close()
        q = make_queue()
        e2 = q.pop()
        assert e1 == e2
        q.close()

    def test_close_open(self, make_queue: Callable[[], ClearableQueue]) -> None:
        """Test closing and re-opening keeps state"""
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        q.push(b"c")
        q.push(b"d")
        q.pop()
        q.pop()
        q.close()
        del q

        q = make_queue()
        assert len(q) == 2
        q.push(b"e")
        q.pop()
        q.pop()
        q.close()
        del q

        q = make_queue()
        assert q.pop() is not None
        assert len(q) == 0
        q.close()

    def test_cleanup(
        self, make_queue: Callable[[], ClearableQueue], qpath: Path
    ) -> None:
        """Test queue dir is removed if queue is empty"""
        q = make_queue()
        values = [b"0", b"1", b"2", b"3", b"4"]
        assert qpath.exists()
        for x in values:
            q.push(x)

        for _ in values:
            q.pop()
        q.close()
        assert not qpath.exists()


class DirectoryTestMixin:
    def test_cleanup_unclean(
        self, make_queue: Callable[[], ClearableQueue], qpath: Path
    ) -> None:
        """Test queue dir is not removed if it contains unexpected content"""
        q = make_queue()
        values = [b"0", b"1", b"2", b"3", b"4"]
        assert qpath.exists()
        for x in values:
            q.push(x)

        unexpected_file = qpath / "unexpected"
        unexpected_file.touch()

        for _ in values:
            q.pop()
        q.close()
        assert qpath.exists()
        assert unexpected_file.exists()


class TestFifoMemoryQueue(FifoTestMixin, QueueTestMixin):
    @pytest.fixture
    def make_queue(self) -> Callable[[], FifoMemoryQueue]:
        return FifoMemoryQueue


class TestLifoMemoryQueue(LifoTestMixin, QueueTestMixin):
    @pytest.fixture
    def make_queue(self) -> Callable[[], LifoMemoryQueue]:
        return LifoMemoryQueue


class TestFifoDiskQueue(
    FifoTestMixin,
    DirectoryTestMixin,
    PersistentTestMixin,
    QueueTestMixin,
):
    @pytest.fixture
    def make_queue(self, qpath: Path) -> Callable[[], FifoDiskQueue]:
        return partial(FifoDiskQueue, qpath, chunksize=self.chunksize)

    def test_not_szhdr(
        self, make_queue: Callable[[], FifoDiskQueue], tmp_path: Path
    ) -> None:
        q = make_queue()
        q.push(b"something")
        with (
            (tmp_path / "empty").open("w+") as empty_file,
            mock.patch.object(q, "tailf", empty_file),
        ):
            assert q.peek() is None
            assert q.pop() is None
        q.close()

    def test_chunks(self, make_queue: Callable[[], FifoDiskQueue], qpath: Path) -> None:
        """Test chunks are created and removed"""
        values = [b"0", b"1", b"2", b"3", b"4"]
        q = make_queue()
        for x in values:
            q.push(x)

        chunks = list(qpath.glob("q*"))
        assert len(chunks) == 5 // self.chunksize + 1
        for _ in values:
            q.pop()

        chunks = list(qpath.glob("q*"))
        assert len(chunks) == 1
        q.close()

    def test_clear_removes_chunks(
        self, make_queue: Callable[[], FifoDiskQueue], qpath: Path
    ) -> None:
        q = make_queue()
        for x in [b"0", b"1", b"2", b"3", b"4"]:
            q.push(x)
        q.clear()
        assert list(qpath.glob("q*")) == [qpath / "q00000"]
        q.close()


class TestChunkSize1FifoDiskQueue(TestFifoDiskQueue):
    chunksize = 1


class TestChunkSize2FifoDiskQueue(TestFifoDiskQueue):
    chunksize = 2


class TestChunkSize3FifoDiskQueue(TestFifoDiskQueue):
    chunksize = 3


class TestChunkSize4FifoDiskQueue(TestFifoDiskQueue):
    chunksize = 4


class TestLifoDiskQueue(LifoTestMixin, PersistentTestMixin, QueueTestMixin):
    @pytest.fixture
    def make_queue(self, qpath: Path) -> Callable[[], LifoDiskQueue]:
        return partial(LifoDiskQueue, qpath)

    def test_file_size_shrinks(
        self, make_queue: Callable[[], LifoDiskQueue], qpath: Path
    ) -> None:
        """Test size of queue file shrinks when popping items"""
        q = make_queue()
        q.push(b"a")
        q.push(b"b")
        q.close()
        size = qpath.stat().st_size
        q = make_queue()
        q.pop()
        q.close()
        assert qpath.stat().st_size, size


class TestFifoSQLiteQueue(FifoTestMixin, PersistentTestMixin, QueueTestMixin):
    @pytest.fixture
    def make_queue(self, qpath: Path) -> Callable[[], FifoSQLiteQueue]:
        return partial(FifoSQLiteQueue, qpath)


class TestLifoSQLiteQueue(LifoTestMixin, PersistentTestMixin, QueueTestMixin):
    @pytest.fixture
    def make_queue(self, qpath: Path) -> Callable[[], LifoSQLiteQueue]:
        return partial(LifoSQLiteQueue, qpath)
