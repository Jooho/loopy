import os
import pytest
from core.env import EnvManager


# Function to get dynamic root path
def get_default_loopy_root_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", "..", ".."))


@pytest.fixture(
    params=[
        (
            "/tmp",
            "custom.yaml",
            "/tmp",
            "/tmp/custom.yaml",
        ),  # When both LOOPY_ROOT_PATH and LOOPY_CONFIG_NAME are set
        (
            None,
            "custom.yaml",
            get_default_loopy_root_path(),
            get_default_loopy_root_path() + "/custom.yaml",
        ),  # When LOOPY_ROOT_PATH is not set
        ("/tmp", None, "/tmp", "/tmp/config.yaml"),  # When LOOPY_CONFIG_PATH is not set
        (
            None,
            None,
            get_default_loopy_root_path(),
            get_default_loopy_root_path() + "/config.yaml",
        ),  # When both are not set
    ]
)
def env_manager_with_params(monkeypatch, request):
    (
        loopy_root_path,
        loopy_config_name,
        expected_loopy_root_path,
        expected_config_path,
    ) = request.param

    if loopy_root_path:
        monkeypatch.setenv("LOOPY_ROOT_PATH", loopy_root_path)
    if loopy_config_name:
        monkeypatch.setenv("LOOPY_CONFIG_NAME", loopy_config_name)

    env_manager = EnvManager()

    # Yield the manager, test logic will come after the fixture
    yield env_manager, expected_loopy_root_path, expected_config_path


@pytest.mark.fvt
@pytest.mark.core
def test_env_manager_initialization(env_manager_with_params):
    # Check if the environment variables are set correctly.
    env_manager, expected_loopy_root_path, expected_config_path = (
        env_manager_with_params
    )

    # Ensure that the environment variables are correctly set
    assert env_manager.get_root_path() == expected_loopy_root_path
    assert env_manager.get_config_path() == expected_config_path


@pytest.mark.fvt
@pytest.mark.core
def test_additional_env_variables():
    env_manager = EnvManager()

    # Check if additional environment variables (commands_dir, cli_dir, etc.) are added correctly.
    additional_keys = ["commands_dir", "cli_dir", "logics_dir", "py_utils_dir"]
    for key in additional_keys:
        assert key in env_manager.get_env()


@pytest.mark.fvt
@pytest.mark.core
def test_loopy_env_vars():
    # Set an environment variable starting with "LOOPY" and check if it's added to the env dictionary.
    os.environ["LOOPY_TEST_VAR"] = "test_value"
    env_manager = (
        EnvManager()
    )  # A new instance to reflect the updated environment variables.

    assert "test_var" in env_manager.get_env()
    assert env_manager.get_env()["test_var"] == "test_value"


@pytest.mark.fvt
@pytest.mark.core
def test_sys_paths():
    env_manager = EnvManager()
    # Check if the necessary directories are added to sys.path.
    import sys

    assert env_manager.commands_dir in sys.path
    assert env_manager.cli_dir in sys.path
    assert env_manager.logics_dir in sys.path
    assert env_manager.py_utils_dir in sys.path
