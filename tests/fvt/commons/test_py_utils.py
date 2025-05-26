import pytest
import os
from unittest.mock import patch
from commons.python.py_utils import (
    die,
    debug,
    info,
    warn,
    error,
    fail,
    success,
    pass_message,
    pending,
    is_positive,
    remove_comment_lines,
    validate_script_params,
)


@pytest.fixture
def mock_subprocess():
    with patch("subprocess.run") as mock:
        yield mock


@pytest.fixture
def mock_os_environ():
    with patch.dict(os.environ, {"STOP_WHEN_FAILED": "yes"}, clear=True):
        yield


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_die(capsys):
    with pytest.raises(SystemExit) as exc_info:
        die("Test error message")
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "[FATAL]: Test error message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_debug(capsys):
    debug("Test debug message")
    captured = capsys.readouterr()
    assert "[DEBUG] Test debug message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_info(capsys):
    info("Test info message")
    captured = capsys.readouterr()
    assert "[INFO] Test info message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_warn(capsys):
    warn("Test warning message")
    captured = capsys.readouterr()
    assert "[WARN] Test warning message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_error(capsys):
    error("Test error message")
    captured = capsys.readouterr()
    assert "[ERROR] Test error message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_fail(capsys):
    fail("Test fail message")
    captured = capsys.readouterr()
    assert "[FAIL] Test fail message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_success(capsys):
    success("Test success message")
    captured = capsys.readouterr()
    assert "[SUCCESS] Test success message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_pass_message(capsys):
    pass_message("Test pass message")
    captured = capsys.readouterr()
    assert "[PASS] Test pass message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_pending(capsys):
    pending("Test pending message")
    captured = capsys.readouterr()
    assert "[PENDING] Test pending message" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
@pytest.mark.parametrize(
    "input_value,expected",
    [
        ("yes", 0),
        ("true", 0),
        ("0", 0),
        (True, 0),
        ("no", 1),
        ("false", 1),
        ("1", 1),
        (False, 1),
    ],
)
def test_is_positive_valid_inputs(input_value, expected):
    assert is_positive(input_value) == expected


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_is_positive_invalid_input():
    with pytest.raises(ValueError):
        is_positive("invalid")


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_is_positive_empty_input():
    with pytest.raises(ValueError):
        is_positive("")


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_remove_comment_lines():
    input_text = """# This is a comment
command1
# Another comment
command2
# Last comment
command3"""
    expected = """command1
command2
command3"""
    assert remove_comment_lines(input_text) == expected


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_empty_input():
    """Test validation with empty input"""
    is_valid, unknown_params = validate_script_params("", ["NAME", "WITH_ISTIO"])
    assert is_valid is True
    assert unknown_params == []


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_valid_params():
    """Test validation with valid parameters"""
    is_valid, unknown_params = validate_script_params(
        "NAME=debug-pod WITH_ISTIO=true", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is True
    assert unknown_params == []


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_single_valid_param():
    """Test validation with single valid parameter"""
    is_valid, unknown_params = validate_script_params(
        "NAME=debug-pod", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is True
    assert unknown_params == []


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_unknown_param():
    """Test validation with unknown parameter"""
    is_valid, unknown_params = validate_script_params(
        "NAME=debug-pod UNKNOWN=value", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is False
    assert unknown_params == ["UNKNOWN"]


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_multiple_unknown_params():
    """Test validation with multiple unknown parameters"""
    is_valid, unknown_params = validate_script_params(
        "NAME=debug-pod UNKNOWN1=value UNKNOWN2=value", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is False
    assert set(unknown_params) == {"UNKNOWN1", "UNKNOWN2"}


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_mixed_valid_invalid():
    """Test validation with mix of valid and invalid parameters"""
    is_valid, unknown_params = validate_script_params(
        "NAME=debug-pod WITH_ISTIO=true UNKNOWN=value", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is False
    assert unknown_params == ["UNKNOWN"]


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_empty_allowed_list():
    """Test validation with empty allowed parameters list"""
    is_valid, unknown_params = validate_script_params("NAME=debug-pod", [])
    assert is_valid is False
    assert unknown_params == ["NAME"]


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_whitespace_handling():
    """Test validation with extra whitespace in input"""
    is_valid, unknown_params = validate_script_params(
        "  NAME=debug-pod   WITH_ISTIO=true  ", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is True
    assert unknown_params == []


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_validate_script_params_case_sensitivity():
    """Test validation with case sensitivity"""
    is_valid, unknown_params = validate_script_params(
        "name=debug-pod", ["NAME", "WITH_ISTIO"]
    )
    assert is_valid is False
    assert unknown_params == ["name"]
