# from click.testing import CliRunner
import yaml
import pytest
import tempfile
import shutil
import os
 
@pytest.fixture
def copied_config_files():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # loopy/
    config_path = os.path.join(base_dir, "config.yaml")
    default_vars_path = os.path.join(base_dir, "commons","default-variables.yaml")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_config_path = os.path.join(tmpdir, "config.yaml")
        shutil.copy(config_path, tmp_config_path)
        
        with open(config_path, "r") as f:
            import yaml
            config_data = yaml.safe_load(f)
            default_vars_file = config_data.get("default_vars_file")
         # If default_vars_file is specified, update the path and copy the file to the temp directory
        if default_vars_file:
            # Update the path of the default_vars_file to the temporary directory
            updated_default_vars_path = os.path.join(tmpdir, "commons", "default-variables.yaml")

            # Ensure the 'commons' directory exists in the temp directory
            os.makedirs(os.path.dirname(updated_default_vars_path), exist_ok=True)

            # Copy the original default_vars_file to the new location in the temp directory
            base_default_vars_path = os.path.join(base_dir, default_vars_file)
            shutil.copy(base_default_vars_path, updated_default_vars_path)

            # Update the config data to reflect the new location of the default_vars_file
            config_data["default_vars_file"] = updated_default_vars_path

        yield tmp_config_path, tmpdir        
        


@pytest.fixture(scope="function", autouse=True)
def loopy_root_path():
    """Returns the default root path of the Loopy project (2 levels up from current file)."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, ".."))        