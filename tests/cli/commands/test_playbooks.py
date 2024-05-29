from click.testing import CliRunner
import pytest
import sys


sys.path.append("./")
sys.path.append("./src/cli/commands")
sys.path.append("./src/cli/logics")
sys.path.append("./commons/python")

from playbooks import list_playbooks, show_playbook, run_playbook

@pytest.mark.cli
@pytest.mark.playbooks
def test_list_playbooks(cli_runner, custom_context):
    result = cli_runner.invoke(list_playbooks, obj=custom_context)
    assert result.exit_code == 0
    assert "Available playbooks:" in result.output
    assert "loopy-test-report-playbook" in result.output

@pytest.mark.cli
@pytest.mark.playbooks
def test_show_playbook(cli_runner, custom_context):
    result = cli_runner.invoke(show_playbook, ["loopy-test-report-playbook"], obj=custom_context)
    assert result.exit_code == 0
    assert "Name: loopy-test-report-playbook" in result.output

# @pytest.mark.cli
# @pytest.mark.playbooks
# def test_run_playbook(cli_runner, custom_context):
#     result = cli_runner.invoke(run_playbook, ["shell-execute","-p","COMMANDS=echo test"], obj=custom_context)
#     # result = cli_runner.invoke(run_playbook, ["shell-execute","-p"], obj=custom_context)
#     print(f"TEST: {result.stdout.strip()}")

#     # assert result.exit_code == 0
#     assert "Success" in result.stdout.strip()
