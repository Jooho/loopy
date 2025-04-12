import pytest

@pytest.mark.cli
@pytest.mark.roles
def test_test_role(cli_runner, loopy_root_path):
    from src.cli.commands.roles import test_role
    result = cli_runner.invoke(test_role, ["test"])
    assert result.exit_code == 0
    assert "Running tests for role: test" in result.output

@pytest.mark.cli
@pytest.mark.roles
def test_list_roles(cli_runner, custom_context):
    from cli.commands.roles import list_roles
    result = cli_runner.invoke(list_roles)
    assert result.exit_code == 0
    assert "Available roles:" in result.output
    assert "cert-generate" in result.output
    assert "minio-deploy" in result.output

@pytest.mark.cli
@pytest.mark.roles
def test_show_role(cli_runner, custom_context):
    from cli.commands.roles import show_role
    result = cli_runner.invoke(show_role, ["minio-deploy"])
    assert result.exit_code == 0
    assert "Name: minio-deploy" in result.output

@pytest.mark.cli
@pytest.mark.roles
def test_run_role(cli_runner, custom_context):
    from cli.commands.roles import run_role
    result = cli_runner.invoke(run_role, ["shell-execute","-p","COMMANDS=echo test","-l","-g"])
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


@pytest.mark.cli
@pytest.mark.roles
def test_run_role_multi_commands(cli_runner, custom_context):
    from cli.commands.roles import run_role
    result = cli_runner.invoke(run_role, ["shell-execute","-p","COMMANDS=echo first %% echo second","-l","-g"])
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()


@pytest.mark.cli
@pytest.mark.roles
def test_run_role_failed(cli_runner, custom_context):
    from cli.commands.roles import run_role
    result = cli_runner.invoke(run_role, ["shell-execute","-p","COMMANDS=\"echo test","-l","-g"])
    assert result.exit_code == 0
    assert " There are some errors" in result.stdout.strip()
