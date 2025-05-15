import pytest
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@pytest.mark.fvt
@pytest.mark.cli
@pytest.mark.cli_playbooks
def test_list_playbooks(cli_runner, loopy_context):
    from src.cli.commands.playbooks import list_playbooks

    result = cli_runner.invoke(list_playbooks, obj=loopy_context)
    assert result.exit_code == 0
    assert "Available playbooks:" in result.output
    assert "loopy-test-report-playbook" in result.output


@pytest.mark.fvt
@pytest.mark.cli
@pytest.mark.cli_playbooks
def test_show_playbook(cli_runner, loopy_context):
    from src.cli.commands.playbooks import show_playbook

    result = cli_runner.invoke(
        show_playbook, ["loopy-unit-tests-non-cluster-units"], obj=loopy_context
    )
    assert result.exit_code == 0
    assert "Name: loopy-unit-tests" in result.output


@pytest.mark.fvt
@pytest.mark.cli
@pytest.mark.cli_playbooks
def test_run_playbook_units(cli_runner, loopy_context):
    from src.cli.commands.playbooks import run_playbook

    result = cli_runner.invoke(
        run_playbook,
        ["loopy-unit-tests-non-cluster-units", "-l", "-g"],
        obj=loopy_context,
    )
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


@pytest.mark.fvt
@pytest.mark.cli
@pytest.mark.cli_playbooks
def test_run_playbook_role_unit(cli_runner, loopy_context):
    from src.cli.commands.playbooks import run_playbook

    result = cli_runner.invoke(
        run_playbook,
        ["loopy-unit-tests-non-cluster-role-unit", "-l", "-g"],
        obj=loopy_context,
    )
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


@pytest.mark.fvt
@pytest.mark.cli
@pytest.mark.cli_playbooks
def test_run_playbook_unit_role(cli_runner, loopy_context):
    from src.cli.commands.playbooks import run_playbook

    result = cli_runner.invoke(
        run_playbook,
        ["loopy-unit-tests-non-cluster-unit-role", "-l", "-g"],
        obj=loopy_context,
    )
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


@pytest.mark.fvt
@pytest.mark.cli
@pytest.mark.cli_playbooks
def test_run_playbook_roles(cli_runner, loopy_context):
    from src.cli.commands.playbooks import run_playbook

    result = cli_runner.invoke(
        run_playbook,
        ["loopy-unit-tests-non-cluster-roles", "-l", "-g"],
        obj=loopy_context,
    )
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


# @pytest.mark.fvt
# @pytest.mark.cli
# @pytest.mark.cli_playbooks
# @pytest.mark.cluster_tests
# def test_run_playbook_kserve_raw(cli_runner, loopy_context, loopy_root_path):
#     from src.cli.commands.playbooks import run_playbook

#     cluster_sh_path = f"{loopy_root_path}/tests/test-data/cluster-info/cluster-crc.sh"
#     result = cli_runner.invoke(
#         run_playbook,
#         ["loopy-unit-tests-on-cluster-install-kserve-raw-on-existing-cluster", "-l", "-g", "-i", cluster_sh_path],
#         obj=loopy_context,
#     )
#     assert result.exit_code == 0
#     assert "Success" in result.stdout.strip()


# @pytest.mark.fvt
# @pytest.mark.cli
# @pytest.mark.cli_playbooks
# def test_run_playbook(cli_runner, custom_context):
#     from src.cli.commands.playbooks import run_playbook

#     result = cli_runner.invoke(run_playbook, ["loopy-unit-tests", "-l", "-g"])
#     assert result.exit_code == 0
#     assert "Success" in result.stdout.strip()

# TO-DO: Environment variable and Parameter handling missing
# Environment variable can overwrite the parameter in the component
# Environment variable must start with LOOPY


# @pytest.mark.fvt
# @pytest.mark.cli
# @pytest.mark.cli_playbooks
# def test_run_playbook_fail_with_stop_when_error_happened_0(cli_runner, custom_context):
#     from src.cli.commands.playbooks import run_playbook
#     result = cli_runner.invoke(run_playbook, ["loopy-fail-unit-tests", "-l", "-g"], env={"STOP_WHEN_FAILED": "0"})
#     if result.exit_code != 0:
#         logging.error(f"Stdout: {result.stdout}")
#     assert result.exit_code == 0
#     assert "Fail" in result.stdout.strip()
