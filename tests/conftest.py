from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_url():
    return lambda name: (FIXTURES / name).resolve().as_uri()
