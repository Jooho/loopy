from click.testing import CliRunner
import pytest
import sys


sys.path.append("./")
sys.path.append("./src/cli/commands")
sys.path.append("./src/cli/logics")
sys.path.append("./commons/python")

from units import list_units, show_unit, run_unit

@pytest.mark.cli
@pytest.mark.units
def test_list_units(cli_runner, custom_context):
    result = cli_runner.invoke(list_units, obj=custom_context)
    assert result.exit_code == 0
    assert "Available units:" in result.output
    assert "loopy-test-cert-generate" in result.output
    assert "loopy-test-kubectl" in result.output

@pytest.mark.cli
@pytest.mark.units
def test_show_unit(cli_runner, custom_context):
    result = cli_runner.invoke(show_unit, ["loopy-test-kubectl"], obj=custom_context)
    assert result.exit_code == 0
    assert "Name: loopy-test-kubectl" in result.output

# @pytest.mark.cli
# @pytest.mark.units
# def test_run_unit(cli_runner, custom_context):
#     result = cli_runner.invoke(run_unit, ["shell-execute","-p","COMMANDS=echo test"], obj=custom_context)
#     # result = cli_runner.invoke(run_unit, ["shell-execute","-p"], obj=custom_context)
#     print(f"TEST: {result.stdout.strip()}")

#     # assert result.exit_code == 0
#     assert "Success" in result.stdout.strip()
