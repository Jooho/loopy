from src.core.config_loader import ConfigLoader
import pytest
import tempfile
import shutil
import os


@pytest.fixture
def copied_config_files():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )  # loopy/../

    config_path = os.path.join(base_dir, "config.yaml")
    internal_config_path = os.path.join(base_dir, "src", "core", "internal_config.yaml")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_config_path = os.path.join(tmpdir, "config.yaml")
        tmp_internal_config_path = os.path.join(
            tmpdir, "src", "core", "internal_config.yaml"
        )
        shutil.copy(config_path, tmp_config_path)
        os.makedirs(os.path.dirname(tmp_internal_config_path), exist_ok=True)
        shutil.copy(internal_config_path, tmp_internal_config_path)

        with open(config_path, "r") as f:
            import yaml

            config_data = yaml.safe_load(f)
            default_vars_file = config_data.get("default_vars_file")
        # If default_vars_file is specified, update the path and copy the file to the temp directory
        if default_vars_file:
            # Update the path of the default_vars_file to the temporary directory
            updated_default_vars_path = os.path.join(
                tmpdir, "src", "commons", "default-variables.yaml"
            )

            # Ensure the 'commons' directory exists in the temp directory
            os.makedirs(os.path.dirname(updated_default_vars_path), exist_ok=True)

            # Copy the original default_vars_file to the new location in the temp directory
            base_default_vars_path = os.path.join(base_dir, default_vars_file)
            shutil.copy(base_default_vars_path, updated_default_vars_path)

            # Update the config data to reflect the new location of the default_vars_file
            config_data["default_vars_file"] = updated_default_vars_path

        yield tmp_config_path, tmpdir


# Test function to validate ConfigLoader with the real files copied to the temp directory
@pytest.mark.fvt
@pytest.mark.core
def test_config_loader_with_real_files(copied_config_files):
    # Get the temp paths for config.yaml and root_path from the fixture
    config_path, root_path = copied_config_files

    # Initialize the ConfigLoader with the copied config file paths
    loader = ConfigLoader(config_path=config_path, loopy_root_path=root_path)
    loader.load()

    # Get the loaded config and default_vars data
    config = loader.get_config()
    default_vars = loader.get_default_vars()

    # Check that the config and default_vars are not None
    assert config is not None, "Config should not be None"
    assert default_vars is not None, "Default vars should not be None"

    # Verify that the config contains the expected keys
    expected_keys_in_config = [
        "default_vars_file",  # Path to the default variables file
        "enable_loopy_report",  # Whether Loopy reports are enabled
        "enable_loopy_logo",  # Whether Loopy logo is enabled
        "enable_loopy_log",  # Whether Loopy logging is enabled
        "ignore_validate_input_env",  # Whether environment validation is ignored
        "keep_env_variables",  # List of environment variables to keep
        "additional_role_dirs",  # Additional directories for roles
        "additional_unit_dirs",  # Additional directories for units
        "additional_playbook_dirs",  # Additional directories for playbooks
        "logging",  # Logging configuration block
    ]

    # Check that each expected key is present in the config
    for key in expected_keys_in_config:
        assert key in config, f"'{key}' should be in config data"

    expected_keys_in_default_vars_files = [
        "operator",  # Under the operator section
        "openshift",  # Under the openshift section
        "opendatahub",  # Under the opendatahub section
        "minio",  # Under the minio section
        "kserve",  # Under the kserve section
        "cert",  # Under the cert section
        "modelmesh",  # Under the modelmesh section
    ]
    # Check that each expected key is present in the default_vars
    for key in expected_keys_in_default_vars_files:
        assert key in default_vars, f"'{key}' should be in default vars"
