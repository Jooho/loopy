import pytest

@pytest.mark.cli
@pytest.mark.playbooks
def test_list_playbooks(cli_runner, custom_context):
    from src.cli.commands.playbooks import list_playbooks
    result = cli_runner.invoke(list_playbooks)
    assert result.exit_code == 0
    assert "Available playbooks:" in result.output
    assert "loopy-test-report-playbook" in result.output

@pytest.mark.cli
@pytest.mark.playbooks
def test_show_playbook(cli_runner, custom_context):
    from src.cli.commands.playbooks import show_playbook
    result = cli_runner.invoke(show_playbook, ["loopy-unit-tests"])
    assert result.exit_code == 0
    assert "Name: loopy-unit-tests" in result.output

# @pytest.mark.cli
# @pytest.mark.playbooks
# def test_run_playbook(cli_runner, custom_context):
#     from src.cli.commands.playbooks import run_playbook
#     result = cli_runner.invoke(run_playbook, ["loopy-unit-tests","-l","-g"])
#     assert result.exit_code == 0
#     assert "Success" in result.stdout.strip()
