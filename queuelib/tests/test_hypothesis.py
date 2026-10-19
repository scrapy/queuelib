from __future__ import annotations

import tempfile
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING, TypeAlias

import pytest
from hypothesis import example, given
from hypothesis import strategies as st

from queuelib import (
    FifoDiskQueue,
    FifoMemoryQueue,
    FifoSQLiteQueue,
    LifoDiskQueue,
    LifoMemoryQueue,
    LifoSQLiteQueue,
    PriorityQueue,
    RoundRobinQueue,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Hashable


# LifoMemoryQueue and LifoSQLiteQueue subclass the Fifo* ones
Queue: TypeAlias = FifoMemoryQueue | FifoDiskQueue | LifoDiskQueue | FifoSQLiteQueue
MEMORY: tuple[type[Queue], ...] = (FifoMemoryQueue, LifoMemoryQueue)
PERSISTENT: tuple[type[Queue], ...] = (
    FifoDiskQueue,
    LifoDiskQueue,
    FifoSQLiteQueue,
    LifoSQLiteQueue,
)


ITEMS: st.SearchStrategy[bytes] = st.binary(max_size=8)
SIMPLE_OPS: st.SearchStrategy[tuple[str, ...]] = st.sampled_from(
    [("pop",), ("peek",), ("clear",), ("reopen",)]
)
PRIOS: st.SearchStrategy[int] = st.integers(-3, 3)
KEYS: st.SearchStrategy[str] = st.sampled_from("ABCD")


def is_lifo(cls: type) -> bool:
    return cls.__name__.startswith("Lifo")


def opener(cls: type[Queue], path: Path, chunksize: int = 3) -> Callable[[], Queue]:
    """Return a callable that opens a *cls* queue at *path*."""
    if issubclass(cls, FifoMemoryQueue):
        return cls
    if issubclass(cls, FifoDiskQueue):
        return lambda: cls(path, chunksize=chunksize)
    return lambda: cls(path)


@pytest.mark.parametrize("cls", [*MEMORY, *PERSISTENT])
@given(
    chunksize=st.integers(1, 5),
    ops=st.lists(st.one_of(st.tuples(st.just("push"), ITEMS), SIMPLE_OPS), max_size=60),
)
def test_queue_matches_deque(
    cls: type[Queue], chunksize: int, ops: list[tuple[str] | tuple[str, bytes]]
) -> None:
    """Compare random sequences of operations on a queue and a ``collections.deque``."""
    lifo = is_lifo(cls)
    model: deque[bytes] = deque()

    def model_pop() -> bytes | None:
        if not model:
            return None
        return model.pop() if lifo else model.popleft()

    with tempfile.TemporaryDirectory() as tmp:
        open_q = opener(cls, Path(tmp, "q"), chunksize)
        q = open_q()
        try:
            for op in ops:
                match op:
                    case ("push", item):
                        q.push(item)
                        model.append(item)
                    case ("pop",):
                        assert q.pop() == model_pop()
                    case ("peek",):
                        head = (model[-1] if lifo else model[0]) if model else None
                        assert q.peek() == head
                    case ("clear",):
                        q.clear()
                        model.clear()
                    case ("reopen",) if cls not in MEMORY:
                        q.close()
                        q = open_q()
                assert len(q) == len(model)
            # Some corruption only shows on a later pop(), so drain the queue.
            while model:
                assert q.pop() == model_pop()
            assert q.pop() is None
        finally:
            q.close()


@pytest.mark.parametrize("cls", [*MEMORY, *PERSISTENT])
@given(
    ops=st.lists(
        st.one_of(
            st.tuples(st.just("push"), ITEMS, PRIOS),
            st.tuples(st.just("badpush"), PRIOS),
            SIMPLE_OPS,
        ),
        max_size=40,
    ),
)
def test_priority_queue_matches_sorted_model(
    cls: type[Queue], ops: list[tuple[str] | tuple[str, int] | tuple[str, bytes, int]]
) -> None:
    """Compare random sequences of operations on a ``PriorityQueue`` and a sorted model."""
    lifo = is_lifo(cls)
    # (priority, seq, item)
    model: list[tuple[int, int, bytes]] = []
    seq = 0

    def model_sort_key(entry: tuple[int, int, bytes]) -> tuple[int, int]:
        prio, seq, _ = entry
        return prio, -seq if lifo else seq

    def model_next() -> tuple[int, int, bytes] | None:
        if not model:
            return None
        return min(model, key=model_sort_key)

    def model_pop() -> bytes | None:
        entry = model_next()
        if entry is None:
            return None
        model.remove(entry)
        return entry[2]

    with tempfile.TemporaryDirectory() as tmp:

        def qfactory(prio: int) -> Queue:
            return opener(cls, Path(tmp, f"p{prio}"))()

        pq = PriorityQueue(qfactory)  # type: ignore[arg-type]
        try:
            for op in ops:
                match op:
                    case ("push", item, prio):
                        pq.push(item, prio)
                        model.append((prio, seq, item))
                        seq += 1
                    case ("badpush", prio) if cls not in MEMORY:
                        with pytest.raises(TypeError):
                            pq.push(object(), prio)
                    case ("pop",):
                        assert pq.pop() == model_pop()
                    case ("peek",):
                        entry = model_next()
                        assert pq.peek() == (entry[2] if entry else None)
                    case ("clear",):
                        pq.clear()
                        model.clear()
                    case ("reopen",) if cls not in MEMORY:
                        active = pq.close()
                        assert sorted(active) == sorted({e[0] for e in model})
                        pq = PriorityQueue(qfactory, active)  # type: ignore[arg-type]
                assert len(pq) == len(model)
            while model:
                assert pq.pop() == model_pop()
            assert pq.pop() is None
        finally:
            pq.close()


@pytest.mark.parametrize("cls", [*MEMORY, *PERSISTENT])
@given(
    ops=st.lists(
        st.one_of(
            st.tuples(st.just("push"), KEYS),
            st.tuples(st.just("badpush"), KEYS),
            SIMPLE_OPS,
        ),
        max_size=40,
    ),
)
def test_round_robin_queue_invariants(
    cls: type[Queue], ops: list[tuple[str] | tuple[str, str]]
) -> None:
    """Check ``RoundRobinQueue`` invariants."""
    lifo = is_lifo(cls)
    # key -> deque of unique items, b"<key><seq>"
    model: dict[str, deque[bytes]] = {}
    seq = 0

    def model_empty() -> bool:
        return not any(model.values())

    with tempfile.TemporaryDirectory() as tmp:

        def qfactory(key: Hashable) -> Queue:
            return opener(cls, Path(tmp, f"k{key}"))()

        rr = RoundRobinQueue(qfactory)  # type: ignore[arg-type]

        def check_pop() -> None:
            peeked = rr.peek()
            item = rr.pop()
            assert peeked == item
            if item is None:
                assert model_empty()
                return
            bucket = model[item[:1].decode()]
            assert item == (bucket.pop() if lifo else bucket.popleft())

        try:
            for op in ops:
                match op:
                    case ("push", key):
                        item = f"{key}{seq}".encode()
                        seq += 1
                        rr.push(item, key)
                        model.setdefault(key, deque()).append(item)
                    case ("badpush", key) if cls not in MEMORY:
                        with pytest.raises(TypeError):
                            rr.push(object(), key)
                    case ("pop",):
                        check_pop()
                    case ("peek",):
                        assert (rr.peek() is None) == model_empty()
                    case ("clear",):
                        rr.clear()
                        model.clear()
                    case ("reopen",) if cls not in MEMORY:
                        active = rr.close()
                        assert set(active) == {k for k, v in model.items() if v}
                        rr = RoundRobinQueue(qfactory, active)  # type: ignore[arg-type]
                assert len(rr) == sum(map(len, model.values()))
            while not model_empty():
                check_pop()
            assert rr.pop() is None
        finally:
            rr.close()


@pytest.mark.xfail(
    reason="PriorityQueue starts at the lowest startprios bucket even if it is empty",
    strict=True,
)
@given(
    filled=st.dictionaries(PRIOS, st.lists(ITEMS, min_size=1, max_size=3)),
    extra=st.lists(PRIOS, max_size=4),
)
@example(filled={1: [b""]}, extra=[0])
def test_priority_queue_startprios_with_empty_buckets(
    filled: dict[int, list[bytes]], extra: list[int]
) -> None:
    """Test ``PriorityQueue`` with some empty buckets in ``startprios``."""
    buckets: dict[int, FifoMemoryQueue] = {}
    for prio, items in filled.items():
        buckets[prio] = FifoMemoryQueue()
        for item in items:
            buckets[prio].push(item)

    def qfactory(prio: int) -> FifoMemoryQueue:
        return buckets.setdefault(prio, FifoMemoryQueue())

    pq = PriorityQueue(qfactory, [*filled, *extra])  # type: ignore[arg-type]
    while len(pq):
        assert pq.peek() is not None
        assert pq.pop() is not None
