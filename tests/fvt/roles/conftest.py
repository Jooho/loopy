import os
import json
import pytest
from pathlib import Path


@pytest.fixture()
def output_root_dir():
    """Fixture providing a temporary output rootdirectory for test outputs"""
    return "/tmp/loopy_fvt_test"


@pytest.fixture()
def output_dir(output_root_dir, role_name):
    """Fixture providing a temporary directory for test outputs"""
    output_dir_path = Path(output_root_dir) / (role_name + "-test")
    output_dir_path.mkdir(parents=True, exist_ok=True)
    return output_dir_path


@pytest.fixture()
def base_env(output_dir, output_root_dir, role_name):
    """Fixture providing base environment variables needed for all tests"""
    return {
        "OUTPUT_ROOT_DIR": str(output_root_dir),
        "OUTPUT_REPORT_FILE": "report",
        "OUTPUT_DATE": "test",
        "ROLE_DIR": str(output_dir / "artifacts" / role_name),
        "REPORT_FILE": str(output_dir / "report"),
        "OUTPUT_DIR": str(output_dir / "output"),
        "OUTPUT_ENV_FILE": str(output_dir / "output" / (role_name + "shell-execute.sh")),
        "LOOPY_RESULT_DIR": str(output_dir / "results"),
        "SHOW_DEBUG_LOG": "false",
        "STOP_WHEN_FAILED": "false",
        "STOP_WHEN_ERROR_HAPPENED": "false",
        "ENABLE_LOOPY_LOG": "true",
        "USE_KIND": "true",
    }


@pytest.fixture
def setup_test_env(base_env, role_name):
    """Fixture providing a helper function to set up test environment"""

    def _setup_test_env(test_env):
        # Create necessary directories
        os.makedirs(base_env["ROLE_DIR"], exist_ok=True)
        os.makedirs(base_env["OUTPUT_DIR"], exist_ok=True)
        os.makedirs(base_env["LOOPY_RESULT_DIR"], exist_ok=True)

        # Create and initialize report files
        Path(base_env["REPORT_FILE"]).touch()
        Path(base_env["OUTPUT_ENV_FILE"]).touch()

        # Initialize role_time.json in the test's result directory
        role_time_data = {"start_time": [], "end_time": []}
        role_time_file = Path(base_env["LOOPY_RESULT_DIR"]) / "role_time.json"
        with open(role_time_file, "w") as f:
            json.dump(role_time_data, f)

        # Initialize summary.json in the test's result directory
        summary_data = {"first_component_type": "role", "first_component_name": role_name, "components": []}
        summary_file = Path(base_env["LOOPY_RESULT_DIR"]) / "summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary_data, f)

        # Set up environment
        env = os.environ.copy()
        env.update(base_env)
        env.update(test_env)
        return env

    return _setup_test_env
