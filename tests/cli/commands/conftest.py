from click.testing import CliRunner
import pytest
import os
import yaml
import shutil
from core.context import LoopyContext
import random
import string

# from core.context import LoopyContextBuilder, set_context, get_context

from core.initializer import Initializer
from core.env import EnvManager
from core.config_loader import ConfigLoader


@pytest.fixture
def cli_runner():
    return CliRunner()


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

    initializer = Initializer(env_list, config_data, default_vars)
    ctx_object = initializer.initialize()
    return LoopyContext(ctx_object)


@pytest.fixture(scope="function")
def cleanup_report_dir(loopy_context):
    yield

    output_root_dir = loopy_context["config"]["output_root_dir"]
    if output_root_dir and os.path.exists(output_root_dir):
        shutil.rmtree(output_root_dir)


def generate_random_name(length=5):
    return "".join(random.choices(string.ascii_lowercase, k=length))
