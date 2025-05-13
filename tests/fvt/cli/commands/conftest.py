from click.testing import CliRunner
import pytest
import os
from cli.commands import utils
from core.context import LoopyContext
from core.initializer import Initializer
from core.env import EnvManager
from core.config_loader import ConfigLoader


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture(scope="function", autouse=True)
def cleanup_report_dir(loopy_context):
    yield

    output_root_dir = loopy_context.config["output_root_dir"]
    if output_root_dir and os.path.exists(output_root_dir):
        try:
            utils.safe_rmtree(output_root_dir)
        except RuntimeError as e:
            pytest.fail(f"Error deleting folder: {e}", pytrace=True)
