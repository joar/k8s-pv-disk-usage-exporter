import logging

import pytest
from disk_usage_exporter import logging as _logging


@pytest.fixture(scope='session', autouse=True)
def configure_logging():
    _logging.configure_logging(for_humans=True, level=logging.DEBUG)
