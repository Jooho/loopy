import os
import json
import pytest
import yaml
import tempfile
import shutil
import types
from pathlib import Path
from unittest.mock import Mock
from core.context import LoopyContext
from core.initializer import Initializer
from core.env import EnvManager
from core.config_loader import ConfigLoader
from tests.conftest import generate_random_name


@pytest.fixture()
def custom_context():
    with open("./tests/custom-context.json", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def copied_config_files():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # loopy/
    config_path = os.path.join(base_dir, "config.yaml")
    default_vars_path = os.path.join(base_dir, "commons", "default-variables.yaml")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_config_path = os.path.join(tmpdir, "config.yaml")
        shutil.copy(config_path, tmp_config_path)

        with open(config_path, "r") as f:
            import yaml

            config_data = yaml.safe_load(f)
            default_vars_file = config_data.get("default_vars_file")
        # If default_vars_file is specified, update the path and copy the file to the temp directory
        if default_vars_file:
            # Update the path of the default_vars_file to the temporary directory
            updated_default_vars_path = os.path.join(
                tmpdir, "commons", "default-variables.yaml"
            )

            # Ensure the 'commons' directory exists in the temp directory
            os.makedirs(os.path.dirname(updated_default_vars_path), exist_ok=True)

            # Copy the original default_vars_file to the new location in the temp directory
            base_default_vars_path = os.path.join(base_dir, default_vars_file)
            shutil.copy(base_default_vars_path, updated_default_vars_path)

            # Update the config data to reflect the new location of the default_vars_file
            config_data["default_vars_file"] = updated_default_vars_path

        yield tmp_config_path, tmpdir


@pytest.fixture(scope="function", autouse=True)
def loopy_root_path():
    """Returns the default root path of the Loopy project (2 levels up from current file)."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, "..", ".."))


@pytest.fixture(autouse=True)
def loopy_context(loopy_root_path):
    envManager = EnvManager()
    config_path = envManager.get_config_path()
    root_path = envManager.get_root_path()
    env_list = envManager.get_env()
    env_list["loopy_root_path"] = loopy_root_path
    env_list["loopy_config_path"] = os.path.join(loopy_root_path, "config.yaml")

    config_loader = ConfigLoader(config_path, root_path)
    config_loader.load()
    config_data = config_loader.get_config()
    default_vars = config_loader.get_default_vars()

    # Set test role/unit/playbook path
    config_data["additional_role_dirs"] = [f"{loopy_root_path}/tests/test-data/roles"]
    config_data["additional_unit_dirs"] = [f"{loopy_root_path}/tests/test-data/units"]
    config_data["additional_playbook_dirs"] = [
        f"{loopy_root_path}/tests/test-data/playbooks"
    ]
    config_data["output_target_dir"] = os.path.join(generate_random_name())

    # Enable input environment validation for testing
    config_data["ignore_validate_input_env"] = False
    initializer = Initializer(env_list, config_data, default_vars)
    ctx_object = initializer.initialize()
    return LoopyContext(ctx_object)


@pytest.fixture
def cli_loopy_ctx(loopy_context, loopy_root_path):
    ctx = types.SimpleNamespace()
    ctx.obj = loopy_context
    ctx.obj.loopy_result_dir = os.path.join(loopy_root_path, "tmp", "loopy_result")
    return ctx


@pytest.fixture
def mock_loopy_ctx(loopy_root_path):
    ctx = Mock()
    ctx.obj.loopy_result_dir = os.path.join(loopy_root_path, "tmp", "loopy_result")
    return ctx
