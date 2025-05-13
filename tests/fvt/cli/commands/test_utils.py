import os
import sys
import types
import pytest
import shutil
import logging
from unittest import mock
from src.cli.commands import utils


# Wrap loopy_context in a SimpleNamespace with an 'obj' attribute
@pytest.fixture
def ctx(loopy_context):
    ctx = types.SimpleNamespace()
    ctx.obj = loopy_context
    ctx.invoke = lambda *args, **kwargs: None  # Mock invoke method
    return ctx


# Test to verify that parameters are correctly checked in a role component.
# This test ensures that the verify_param_in_component function correctly identifies
# if a given parameter exists in the specified role's input environment.
@pytest.mark.fvt
@pytest.mark.cli
def test_verify_param_in_component_role(tmp_path, ctx):
    # Setup dummy role config
    config_path = tmp_path / "role1/config.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("role:\n  input_env:\n    - name: TEST")
    component_list = [{"name": "role1", "path": str(config_path.parent)}]
    params = {"TEST": "val"}
    with mock.patch("yaml.safe_load", return_value={"role": {"input_env": [{"name": "TEST"}]}}):
        utils.verify_param_in_component(ctx, params, "role1", component_list, "role")


# Test to verify that input environment parameters are correctly checked in a role.
# This test ensures that the check_input_env_in_role function correctly identifies
# if a given parameter exists in the role's input environment.
@pytest.mark.fvt
@pytest.mark.cli
def test_check_input_env_in_role(ctx):
    params = ["FOO"]
    role_input_env = [{"name": "FOO"}, {"name": "BAR"}]
    assert utils.check_input_env_in_role(ctx, params, role_input_env)
    params = ["BAZ"]
    assert not utils.check_input_env_in_role(ctx, params, role_input_env)


# Test to verify that logging is configured correctly with the specified verbosity.
# This test ensures that the configure_logging function sets the correct log level
# based on the provided verbosity.
@pytest.mark.fvt
@pytest.mark.cli
def test_configure_logging(ctx):
    level = utils.configure_logging(ctx, verbose=3)
    assert level == logging.DEBUG


# Test to verify that a component exists in the provided list.
# This test ensures that the verify_component_exist function correctly identifies
# if a component exists in the provided list.
@pytest.mark.fvt
@pytest.mark.cli
def test_verify_component_exist_found():
    component_list = [{"name": "foo", "path": "/tmp"}]
    utils.verify_component_exist("foo", component_list)


# Test to verify that a component does not exist in the provided list.
# This test ensures that the verify_component_exist function raises a SystemExit
# when a component does not exist in the provided list.
@pytest.mark.fvt
@pytest.mark.cli
def test_verify_component_exist_not_found():
    component_list = [{"name": "foo", "path": "/tmp"}]
    with pytest.raises(SystemExit):
        utils.verify_component_exist("bar", component_list)


# Test to verify that key-value pairs are parsed correctly.
# This test ensures that the parse_key_value_pairs function correctly parses
# key-value pairs from a list of strings.
@pytest.mark.fvt
@pytest.mark.cli
def test_parse_key_value_pairs():
    ctx = None
    param = None
    value = ["foo=bar", "baz=qux"]
    result = utils.parse_key_value_pairs(ctx, param, value)
    assert result == {"foo": "bar", "baz": "qux"}
    value = ["foo=bar=baz"]
    result = utils.parse_key_value_pairs(ctx, param, value)
    assert result == {"foo": "bar=baz"}
    assert utils.parse_key_value_pairs(ctx, param, None) == {}


# Test to verify that environment variables are loaded from a file if it exists.
# This test ensures that the load_env_file_if_exist function correctly loads
# environment variables from a file and handles non-existent files.
@pytest.mark.fvt
@pytest.mark.cli
def test_load_env_file_if_exist(tmp_path):
    env_file = tmp_path / "envfile"
    env_file.write_text('FOO=bar\nBAR="baz"\n# comment\n')
    result = utils.load_env_file_if_exist(str(env_file))
    assert result == {"FOO": "bar", "BAR": "baz"}
    assert utils.load_env_file_if_exist(None) == {}
    with pytest.raises(SystemExit):
        utils.load_env_file_if_exist("/not/exist/file")


# Test to verify that environment variables are set from a file if it exists.
# This test ensures that the set_env_vars_if_file_exist function correctly sets
# environment variables from a file.
@pytest.mark.fvt
@pytest.mark.cli
def test_set_env_vars_if_file_exist(tmp_path):
    env_file = tmp_path / "envfile"
    env_file.write_text("FOO=bar\nBAR=baz\n")
    utils.set_env_vars_if_file_exist(str(env_file))
    assert os.environ["FOO"] == "bar"
    assert os.environ["BAR"] == "baz"


# Test to verify that parameters are updated with input file values.
# This test ensures that the update_params_with_input_file function correctly updates
# parameters with values from an input file.
@pytest.mark.fvt
@pytest.mark.cli
def test_update_params_with_input_file():
    params = {"A": "1"}
    additional = {"B": "2"}
    result = utils.update_params_with_input_file(additional.copy(), params)
    assert result["A"] == "1"
    assert result["B"] == "2"
    result = utils.update_params_with_input_file({}, params)
    assert result == params


# Test to verify that configuration data is retrieved from a config file directory.
# This test ensures that the get_config_data_by_config_file_dir function correctly retrieves
# configuration data from a specified directory.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_config_data_by_config_file_dir(tmp_path, ctx):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("foo: bar")
    result = utils.get_config_data_by_config_file_dir(ctx, str(tmp_path))
    assert result == {"foo": "bar"}


# Test to verify that an error is raised when a config file is not found.
# This test ensures that the get_config_data_by_config_file_dir function raises an error
# when the specified config file does not exist.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_config_data_by_config_file_dir_not_found(ctx):
    with mock.patch.object(ctx, "invoke") as m:
        utils.get_config_data_by_config_file_dir(ctx, "/not/exist")
        m.assert_called()


# Test to verify that configuration data is retrieved by name for a role.
# This test ensures that the get_config_data_by_name function correctly retrieves
# configuration data for a specified role.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_config_data_by_name_role(tmp_path, ctx):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("role:\n  foo: bar")
    ctx.obj.config["role_list"] = [{"name": "r1", "path": str(tmp_path)}]
    with mock.patch("src.cli.commands.utils.get_config_data_by_config_file_dir", return_value={"role": {"foo": "bar"}}):
        result = utils.get_config_data_by_name(ctx, "r1", "role", ctx.obj.config["role_list"])
        assert result == {"role": {"foo": "bar"}}


# Test to verify that an error is raised when a component is not found by name.
# This test ensures that the get_config_data_by_name function raises an error
# when the specified component is not found.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_config_data_by_name_not_found(ctx):
    with mock.patch.object(ctx, "invoke") as m, pytest.raises(SystemExit):
        utils.get_config_data_by_name(ctx, "notfound", "role", [])
        m.assert_called()


# Test to verify that input environment is retrieved from config data.
# This test ensures that the get_input_env_from_config_data function correctly retrieves
# the input environment from the provided config data.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_input_env_from_config_data():
    assert utils.get_input_env_from_config_data({"input_env": 123}) == 123
    assert utils.get_input_env_from_config_data({}) is None


# Test to verify that input environment is retrieved from unit config data.
# This test ensures that the get_input_env_from_unit_config_data function correctly retrieves
# the input environment from the provided unit config data.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_input_env_from_unit_config_data():
    assert utils.get_input_env_from_unit_config_data({"input_env": 456}) == 456
    assert utils.get_input_env_from_unit_config_data({}) is None


# Test to verify that the first role name in a unit is retrieved correctly.
# This test ensures that the get_first_role_name_in_unit_by_unit_name function correctly retrieves
# the first role name from a unit.
@pytest.mark.fvt
@pytest.mark.cli
def test_get_first_role_name_in_unit_by_unit_name():
    units = [{"name": "u1", "role_name": "r1"}]
    assert utils.get_first_role_name_in_unit_by_unit_name("u1", units) == "r1"
    assert utils.get_first_role_name_in_unit_by_unit_name("u2", units) is None


# Test to verify that the description is retrieved for a role.
# This test ensures that the getDescription function correctly retrieves
# the description for a specified role.
@pytest.mark.fvt
@pytest.mark.cli
def test_getDescription_role(ctx):
    with mock.patch("src.cli.commands.utils.get_config_data_by_name", return_value={"role": {"description": "desc"}}):
        desc = utils.getDescription(ctx, "r1", "role")
        assert desc == "desc"


# Test to verify that the description is retrieved for a unit.
# This test ensures that the getDescription function correctly retrieves
# the description for a specified unit.
@pytest.mark.fvt
@pytest.mark.cli
def test_getDescription_unit(ctx):
    with mock.patch("src.cli.commands.utils.get_config_data_by_name", return_value={"unit": {"description": "udesc"}}):
        desc = utils.getDescription(ctx, "u1", "unit")
        assert desc == "udesc"


# Test to verify that the description is retrieved for a playbook.
# This test ensures that the getDescription function correctly retrieves
# the description for a specified playbook.
@pytest.mark.fvt
@pytest.mark.cli
def test_getDescription_playbook(ctx):
    with mock.patch(
        "src.cli.commands.utils.get_config_data_by_name", return_value={"playbook": {"description": "pdesc"}}
    ):
        desc = utils.getDescription(ctx, "p1", "playbook")
        assert desc == "pdesc"


# Test to verify that a directory is safely removed.
# This test ensures that the safe_rmtree function correctly removes a directory
# and handles dangerous paths appropriately.
@pytest.mark.fvt
@pytest.mark.cli
def test_safe_rmtree(tmp_path):
    d = tmp_path / "dir"
    d.mkdir()
    (d / "f").write_text("x")
    utils.safe_rmtree(str(d))
    assert not d.exists()
    with pytest.raises(ValueError):
        utils.safe_rmtree("")
    for dangerous in ["/", "/home", "/root", "/usr", "/etc", os.path.expanduser("~")]:
        with pytest.raises(RuntimeError):
            utils.safe_rmtree(dangerous)


# Test to verify that the logo is printed without errors.
# This test ensures that the print_logo function runs without raising any errors.
@pytest.mark.fvt
@pytest.mark.cli
def test_print_logo():
    # Just ensure it runs without error
    utils.print_logo()
