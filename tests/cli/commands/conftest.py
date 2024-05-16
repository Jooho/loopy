from click.testing import CliRunner
import pytest
import yaml

@pytest.fixture
def custom_context():
    with open("./tests/custom-context.json", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def cli_runner():
    return CliRunner()
