from click.testing import CliRunner
import pytest
import os
import yaml
import shutil
from core.context import LoopyContextBuilder, set_context, get_context


@pytest.fixture(scope="session", autouse=True)
def custom_context():
    with open("./tests/custom-context.json", "r") as f:
        return yaml.safe_load(f)


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="session", autouse=True)
def setup(custom_context, loopy_root_path,cleanup_report_dir):
    # initialize_global_context
    custom_context["config"]["loopy_root_path"] = loopy_root_path
    custom_context["config"]["loopy_config_path"] = os.path.join(loopy_root_path, "config.yaml")

    context = LoopyContextBuilder(env_list=custom_context["env"], default_vars=custom_context["default_vars"], config_data=custom_context["config"]).build()
    set_context(context)

@pytest.fixture(scope="session",autouse=True)
def cleanup_report_dir():
    yield
    context = get_context()
    output_root_dir = context["config"]["output_root_dir"]
    if output_root_dir and os.path.exists(output_root_dir):
        shutil.rmtree(output_root_dir)
