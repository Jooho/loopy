# tests/test_context.py
import pytest
from core.context import LoopyContextBuilder  # 실제 import 경로에 맞게 수정

@pytest.fixture
def sample_data():
    default_vars = {"var1": "value1", "var2": "value2"}
    config_data = {"key1": "data1", "key2": "data2"}
    return default_vars, config_data

def test_loopy_context_builder(sample_data):
    default_vars, config_data = sample_data
    
    context_builder = LoopyContextBuilder(default_vars, config_data)
    
    result = context_builder.build()

    expected_result = {
        "config": {
            "default_vars": default_vars,
            "config_data": config_data,
        }
    }

    assert result == expected_result, f"Expected {expected_result}, but got {result}"
