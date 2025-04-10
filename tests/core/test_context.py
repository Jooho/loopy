import pytest
from core.context import LoopyContextBuilder


@pytest.fixture
def default_vars():
    return {"key1": "value1", "key2": "value2"}


@pytest.fixture
def config_data():
    return {"config_key1": "config_value1", "config_key2": "config_value2"}


@pytest.fixture
def env_list():
    # Create env_list and add LOOPY_ROOT_PATH
    return {
        "LOOPY_ROOT_PATH": "tmpdir",  # Assuming tmpdir is the root path for Loopy
    }


@pytest.mark.core
def test_loopy_context_builder():
    context_builder = LoopyContextBuilder(env_list, default_vars, config_data)
    result = context_builder.build()

    expected_result = {
        "default_vars": default_vars,
        "config": config_data,
        "env": env_list,
    }

    assert result == expected_result, f"Expected {expected_result}, but got {result}"
