import pytest
import os
import sys
from unittest.mock import patch, MagicMock
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
    stop_when_error_happended,
    remove_comment_lines,
    check_pod_status,
    wait_pod_containers_ready,
    wait_for_pods_ready,
    wait_for_pod_name_ready,
    wait_for_just_created_pod_ready,
    wait_for_csv_installed,
    oc_wait_object_availability,
    oc_wait_return_true,
    get_root_directory,
    check_if_result,
    check_oc_status,
    check_rosa_access,
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
def test_check_pod_status_success(mock_subprocess):
    mock_subprocess.return_value = MagicMock(
        returncode=0,
        stdout='{"items": [{"status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]}}]}',
    )
    assert check_pod_status("app=test", "test-namespace") is True


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_check_pod_status_failure(mock_subprocess):
    mock_subprocess.return_value = MagicMock(returncode=1)
    assert check_pod_status("app=test", "test-namespace") is False


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_wait_pod_containers_ready_success(mock_subprocess):
    mock_subprocess.side_effect = [
        MagicMock(stdout="pod-1"),
        MagicMock(stdout="1"),
        MagicMock(stdout="1"),
    ]
    wait_pod_containers_ready("app=test", "test-namespace")


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_wait_for_pods_ready_success(mock_subprocess):
    # First call: oc get pods -l app=test -n test-namespace -o jsonpath='{.items[*]}'
    # Second call: oc get pods -l app=test -n test-namespace
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stdout="pod-1"),  # First call returns pod name
        MagicMock(
            returncode=0,
            stdout='{"items": [{"status": {"phase": "Running", "conditions": [{"type": "Ready", "status": "True"}]}}]}',
        ),  # Second call returns pod status
    ]
    assert wait_for_pods_ready("app=test", "test-namespace") is True


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_wait_for_pod_name_ready_success(mock_subprocess):
    mock_subprocess.side_effect = [MagicMock(returncode=0), MagicMock(returncode=0)]
    assert wait_for_pod_name_ready("test-pod", "test-namespace") == 0


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_wait_for_csv_installed_success(mock_subprocess):
    mock_subprocess.side_effect = [MagicMock(stdout="Succeeded")]
    wait_for_csv_installed("test-csv", "test-namespace")


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_oc_wait_object_availability_success(mock_subprocess):
    mock_subprocess.return_value = MagicMock(returncode=0)
    oc_wait_object_availability("test-command", 1, 1)


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_oc_wait_return_true_success(mock_subprocess):
    mock_subprocess.return_value = MagicMock(returncode=0)
    assert oc_wait_return_true("test-command", 1, 1) == 0


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_get_root_directory():
    with patch("os.path.isdir") as mock_isdir:
        mock_isdir.return_value = True
        with patch("os.path.dirname") as mock_dirname:
            mock_dirname.return_value = "/test/root"
            assert get_root_directory() == "/test/root"


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_check_if_result_success(capsys):
    check_if_result(0)
    captured = capsys.readouterr()
    assert "PASS" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_check_if_result_failure(capsys):
    with pytest.raises(SystemExit):
        check_if_result(1)
    captured = capsys.readouterr()
    assert "FAIL" in captured.out


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_check_oc_status_success(mock_subprocess):
    mock_subprocess.side_effect = [
        MagicMock(returncode=0, stdout="test-user"),
        MagicMock(stdout="test-group test-user"),
        MagicMock(stdout='{"items": [{"subjects": [{"name": "test-user"}]}]}'),
    ]
    check_oc_status()


@pytest.mark.fvt
@pytest.mark.non_cluster_tests
@pytest.mark.common
def test_check_rosa_access_success(mock_subprocess):
    with patch("os.path.isdir") as mock_isdir, patch("os.path.isfile") as mock_isfile:
        mock_isdir.return_value = True
        mock_isfile.return_value = True
        mock_subprocess.side_effect = [MagicMock(returncode=0), MagicMock(returncode=0)]
        check_rosa_access()
