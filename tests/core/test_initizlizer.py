import os
import pytest
from unittest import mock
from unittest.mock import patch, mock_open
from core.initializer import Initializer


# Fixture to provide mock environment and config
@pytest.fixture
def mock_env_and_config():
    env_list = {"loopy_root_path": "/mock/loopy", "loopy_config_path": "/mock/loopy/config.yaml"}  # Environment variables will be lowcased
    config_data = {
        "output_root_dir": "/tmp/ms_cli",
        "output_env_dir": "output",
        "output_artifacts_dir": "artifacts",
        "output_report_file": "report",
        "show_debug_log": "false",
        "stop_when_failed": "true",
        "stop_when_error_happened": "false",
        "additional_role_dirs": ["/mock/custom/role_dir"],
        "additional_unit_dirs": ["/mock/custom/unit_dir"],
        "additional_playbook_dirs": ["/mock/custom/playbook_dir"],
    }
    default_vars = {"var1": "value1"}

    return env_list, config_data, default_vars


# Test for the initialization of directories and environment variables
@pytest.mark.core
def test_initializer_initialization(mock_env_and_config):
    env_list, config_data, default_vars = mock_env_and_config

    # Mocking os.makedirs and open calls to avoid file system changes
    with mock.patch("os.makedirs") as mock_makedirs, mock.patch("builtins.open", mock.mock_open()) as mock_open:
        # Initialize the Initializer
        initializer = Initializer(env_list, config_data, default_vars)
        initializer.initialize()

        # Check if the directories are being created
        output_dir = config_data["output_dir"]
        artifacts_dir = config_data["artifacts_dir"]
        report_file = config_data["report_file"]

        mock_makedirs.assert_any_call(output_dir, exist_ok=True)
        mock_makedirs.assert_any_call(artifacts_dir, exist_ok=True)

        # Check if the report file is being created
        mock_open.assert_called_with(report_file, "w")

        # Check if the environment variables are set correctly
        assert os.environ["OUTPUT_DIR"] == output_dir
        assert os.environ["ARTIFACTS_DIR"] == artifacts_dir
        assert os.environ["REPORT_FILE"] == report_file


# Test for sync_env_to_config method
@pytest.mark.core
def test_sync_env_to_config(mock_env_and_config):
    env_list, config_data, _ = mock_env_and_config
    initializer = Initializer(env_list, config_data, {})

    # Calling sync_env_to_config method to sync env variables to config
    initializer.sync_env_to_config(env_list, config_data)

    # Check if the config_data is updated with environment variables
    assert config_data["loopy_root_path"] == "/mock/loopy"
    assert config_data["loopy_config_path"] == "/mock/loopy/config.yaml"


# Test for initialize_list method for role
@pytest.mark.core
def test_initialize_list_role(mock_env_and_config):
    # Test Data
    env_list, config_data, default_vars = mock_env_and_config
    config_data["default_roles_dir"] = os.path.join(env_list["loopy_root_path"], "default_provided_services", "roles")
    config_data["default_units_dir"] = os.path.join(env_list["loopy_root_path"], "default_provided_services", "units")
    config_data["default_playbooks_dir"] = os.path.join(env_list["loopy_root_path"], "default_provided_services", "playbooks")

    initializer = Initializer(env_list, config_data, default_vars)

    mock_walk = [
        (config_data["default_roles_dir"] + "/foo", [], ["config.yaml"]),
        (config_data["default_roles_dir"] + "/bar", [], ["config.yaml"]),
        ("/mock/custom/role_dir/foo_2", [], ["config.yaml"]),
        ("/mock/custom/role_dir/bar_2", [], ["config.yaml"]),
    ]

    mock_yaml_data = {"role": {"name": "test"}}

    with patch("os.walk", return_value=mock_walk), patch("builtins.open", mock_open(read_data="fake_yaml_content")), patch(
        "yaml.safe_load", return_value=mock_yaml_data
    ), patch.object(initializer, "validate_config_yaml_schema", return_value=[]):

        initializer.initialize_component_list("role")

        # It is double because it checks additional role dir as well.
        expected_list = [
            {"name": "test", "path": "/mock/loopy/default_provided_services/roles/foo"},
            {"name": "test", "path": "/mock/loopy/default_provided_services/roles/bar"},
            {"name": "test", "path": "/mock/custom/role_dir/foo_2"},
            {"name": "test", "path": "/mock/custom/role_dir/bar_2"},
            {"name": "test", "path": "/mock/loopy/default_provided_services/roles/foo"},
            {"name": "test", "path": "/mock/loopy/default_provided_services/roles/bar"},
            {"name": "test", "path": "/mock/custom/role_dir/foo_2"},
            {"name": "test", "path": "/mock/custom/role_dir/bar_2"},
        ]
        assert initializer.config_data["role_list"] == expected_list


# Test for validate_config_yaml_schema method with mock schema validation
@pytest.mark.core
def test_validate_config_yaml_schema(mock_env_and_config, loopy_root_path):
    env_list, config_data, default_vars = mock_env_and_config
    # Add Schema paths
    config_data["schema"] = {
        "role": f"{loopy_root_path}/src/schema/role.yaml",
        "unit": f"{loopy_root_path}/src/schema/unit.yaml",
        "playbook": f"{loopy_root_path}/src/schema/playbook.yaml",
    }

    initializer = Initializer(env_list, config_data, default_vars)
    # Role
    errors = initializer.validate_config_yaml_schema(f"{loopy_root_path}/tests/test-data/schema/success-role-config.yaml", "role")
    assert len(errors) == 0  # No errors should be present

    errors = initializer.validate_config_yaml_schema(f"{loopy_root_path}/tests/test-data/schema/fail-role-config.yaml", "role")
    assert len(errors) == 1
    assert errors[0]["message"] == "'role' is a required property"

    # Unit
    errors = initializer.validate_config_yaml_schema(f"{loopy_root_path}/tests/test-data/schema/success-unit-config.yaml", "unit")
    assert len(errors) == 0  # No errors should be present

    errors = initializer.validate_config_yaml_schema(f"{loopy_root_path}/tests/test-data/schema/fail-unit-config.yaml", "unit")
    assert len(errors) == 1
    assert errors[0]["message"] == "Additional properties are not allowed ('description2' was unexpected)"

    # Playbook
    errors = initializer.validate_config_yaml_schema(f"{loopy_root_path}/tests/test-data/schema/success-playbook-config.yaml", "playbook")
    assert len(errors) == 0  # No errors should be present

    errors = initializer.validate_config_yaml_schema(f"{loopy_root_path}/tests/test-data/schema/fail-playbook-config.yaml", "playbook")
    assert len(errors) == 1
    assert errors[0]["message"] == "Additional properties are not allowed ('name2' was unexpected)"
