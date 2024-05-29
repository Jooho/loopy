from click.testing import CliRunner
import sys
import pytest

sys.path.append("./")
sys.path.append("./src/cli/commands")
sys.path.append("./src/cli/logics")
sys.path.append("./commons/python")


from roles import test_role, list_roles, show_role, run_role

@pytest.mark.cli
@pytest.mark.roles
def test_test_role(cli_runner, custom_context):
    result = cli_runner.invoke(test_role, ["test"], obj=custom_context)
    assert result.exit_code == 0
    assert "Running tests for role" in result.output

@pytest.mark.cli
@pytest.mark.roles
def test_list_roles(cli_runner, custom_context):
    result = cli_runner.invoke(list_roles, obj=custom_context)
    assert result.exit_code == 0
    assert "Available roles:" in result.output
    assert "cert-generate" in result.output
    assert "minio-deploy" in result.output

@pytest.mark.cli
@pytest.mark.roles
def test_show_role(cli_runner, custom_context):
    result = cli_runner.invoke(show_role, ["minio-deploy"], obj=custom_context)
    assert result.exit_code == 0
    assert "Name: minio-deploy" in result.output

# @pytest.mark.cli
# @pytest.mark.roles
# def test_run_role(cli_runner, custom_context):
#     result = cli_runner.invoke(run_role, ["shell-execute","-p","COMMANDS=echo test"], obj=custom_context)
#     # result = cli_runner.invoke(run_role, ["shell-execute","-p"], obj=custom_context)
#     print(f"TEST: {result.stdout.strip()}")

#     # assert result.exit_code == 0
#     assert "Success" in result.stdout.strip()
