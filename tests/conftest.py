import os
import sys
import time

import pytest


@pytest.fixture
def tmp_module(tmp_path):
    module_path = os.fsdecode(tmp_path)
    sys.path.insert(0, module_path)
    yield module_path
    sys.path.remove(module_path)

@pytest.fixture(autouse=True)
def slow_down_tests():
    yield
    time.sleep(1)
