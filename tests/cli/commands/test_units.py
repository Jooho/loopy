import pytest

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
    result = cli_runner.invoke(run_unit, ["loopy-roles-test-non-cluster-shell-execute","-l","-g"])
    assert result.exit_code == 0
    assert "Success" in result.stdout.strip()
