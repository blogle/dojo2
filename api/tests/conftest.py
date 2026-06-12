from __future__ import annotations

import pytest

from dojo.service import DojoService


@pytest.fixture
def service(tmp_path) -> DojoService:
    dojo_service = DojoService(str(tmp_path / "dojo-test.duckdb"))
    yield dojo_service
    dojo_service.close()


@pytest.fixture
def imported_service(service: DojoService) -> DojoService:
    result = service.import_sheet_data(source="fixture://default", source_kind="fixture")
    assert result["ok"] is True
    return service
