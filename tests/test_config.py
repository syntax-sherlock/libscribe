import os

import pytest

from config import get_env_var


def test_get_env_var():
    os.environ["TEST_VAR"] = "test_value"
    assert get_env_var("TEST_VAR") == "test_value"
    with pytest.raises(ValueError):
        get_env_var("NON_EXISTENT_VAR")
