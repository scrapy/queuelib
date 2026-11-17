from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def qpath(tmp_path: Path) -> Path:
    """Path for a single queue; it does not exist until the queue is created."""
    return tmp_path / "queue"
