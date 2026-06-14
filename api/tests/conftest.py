from __future__ import annotations

import pytest

from dojo.service import DojoService
from tests.support.clock import MutableClock, default_test_clock
from tests.support.database import build_service


@pytest.fixture
def clock() -> MutableClock:
    return default_test_clock()


@pytest.fixture
def service(tmp_path, clock: MutableClock) -> DojoService:
    dojo_service = build_service(tmp_path, clock)
    yield dojo_service
    dojo_service.close()


@pytest.fixture
def imported_service(service: DojoService) -> DojoService:
    result = service.import_sheet_data(source="fixture://default", source_kind="fixture")
    assert result["ok"] is True
    return service
