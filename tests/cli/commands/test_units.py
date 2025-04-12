import pytest
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.mark.cli
@pytest.mark.units
def test_list_units(cli_runner, custom_context):
    from src.cli.commands.units import list_units

    result = cli_runner.invoke(list_units)
    assert result.exit_code == 0
    assert "Available units:" in result.output
    assert "deploy-ssl-minio" in result.output
    assert "loopy-roles-test-non-cluster-shell-execute" in result.output


@pytest.mark.cli
@pytest.mark.units
def test_show_unit(cli_runner, custom_context):
    from src.cli.commands.units import show_unit

    result = cli_runner.invoke(show_unit, ["loopy-roles-test-non-cluster-shell-execute"])
    assert result.exit_code == 0
    assert "Name: loopy-roles-test-non-cluster-shell-execute" in result.output


@pytest.mark.cli
@pytest.mark.units
def test_run_unit(cli_runner, custom_context):
    from src.cli.commands.units import run_unit

    result = cli_runner.invoke(run_unit, ["loopy-roles-test-non-cluster-shell-execute", "-l", "-g"])
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


# TO-DO: Environment variable and Parameter handling missing
# Environment variable can overwrite the parameter in the component
# Environment variable must start with LOOPY

# @pytest.mark.cli
# @pytest.mark.units
# def test_run_unit_fail_with_stop_when_error_happened_1(cli_runner, custom_context):
#     """Report an warn if the executed test role fails  with STOP_WHEN_FAILED = 1"""
#     from src.cli.commands.units import run_unit

#     result = cli_runner.invoke(run_unit, ["loopy-roles-test-non-cluster-fail-test-shell-execute", "-l", "-g"], env={"STOP_WHEN_FAILED": "1"})
#     if result.exit_code != 0:
#        logging.error(f"Stdout: {result.stdout}")
#     assert result.exit_code == 0
#     assert "[WARN] There are some errors" in result.stdout.strip()


# @pytest.mark.cli
# @pytest.mark.units
# def test_run_unit_fail_with_stop_when_error_happened_0(cli_runner, custom_context):
#     """Report an error if the executed test role fails with STOP_WHEN_FAILED = 0"""
#     from src.cli.commands.units import run_unit

#     result = cli_runner.invoke(run_unit, ["loopy-roles-test-non-cluster-fail-test-shell-execute", "-l", "-g"], env={"STOP_WHEN_FAILED": "0"})
#     if result.exit_code != 0:
#         logging.error(f"Stdout: {result.stdout}")
#     assert result.exit_code == 0
#     assert "[FATAL]: STOP_WHEN_ERROR_HAPPENED(0) is set and there are some errors detected, stopping all processes." in result.stdout.strip()


@pytest.mark.cli
@pytest.mark.units
def test_run_unit_non_exist_unit(cli_runner, custom_context):
    from src.cli.commands.units import run_unit

    result = cli_runner.invoke(run_unit, ["NOT-EXIST-UNIT", "-l", "-g"])
    assert result.exit_code == 1
    assert "Unit name(NOT-EXIST-UNIT) does not exist" in result.stdout.strip()
