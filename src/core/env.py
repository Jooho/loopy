import os
import sys


class EnvManager:

    def __init__(self):
        """
        Initialize environment manager, collecting LOOPY-prefixed environment variables
        and setting up paths for configuration and module imports.
        """
        self.env = self.add_loopy_env_vars()

        if not self.env.get("loopy_root_path"):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.loopy_root_path = os.path.abspath(
                os.path.join(current_dir, "..", "..")
            )
            self.env["loopy_root_path"] = self.loopy_root_path

        if not self.env.get("loopy_config_name"):
            self.loopy_config_name = os.environ.get("LOOPY_CONFIG_NAME", "config.yaml")
            self.env["loopy_config_name"] = self.loopy_config_name

        self.loopy_root_path = self.env["loopy_root_path"]
        self.loopy_config_name = self.env["loopy_config_name"]
        self.loopy_config_path = os.path.join(
            self.loopy_root_path, self.loopy_config_name
        )
        self.commands_dir = os.path.join(self.loopy_root_path, "src", "cli", "commands")
        self.cli_dir = os.path.join(self.loopy_root_path, "src", "cli")
        self.logics_dir = os.path.join(self.loopy_root_path, "src", "cli", "logics")
        self.py_utils_dir = os.path.join(self.loopy_root_path, "commons", "python")

        # Add python path
        self.setup_sys_paths()
        self.add_additional_env()

    def setup_sys_paths(self):
        sys.path.append(self.commands_dir)
        sys.path.append(self.cli_dir)
        sys.path.append(self.logics_dir)
        sys.path.append(self.py_utils_dir)

    def add_additional_env(self):
        additional_env = {
            "loopy_config_name": self.loopy_config_name,
            "commands_dir": self.commands_dir,
            "cli_dir": self.cli_dir,
            "logics_dir": self.logics_dir,
            "py_utils_dir": self.py_utils_dir,
        }
        self.env.update(additional_env)

    # Add loopy env vars to the env dictionary
    def add_loopy_env_vars(self):
        env = {}
        for key, value in os.environ.items():
            if key.startswith("LOOPY"):
                if key != "LOOPY_ROOT_PATH":
                    env[key[6:].lower()] = value
                else:
                    env[key.lower()] = value
        return env

    def get_config_path(self):
        return self.loopy_config_path

    def get_root_path(self):
        return self.loopy_root_path

    def get_env(self):
        return self.env

    def update_env_from_system_if_config_key_exists(self, config_data: dict):
        """
        Update internal env dictionary with values from system environment variables (os.environ)
        if the corresponding key exists in the configuration.
        """
        # Add matching environment variables to env
        for config_key in config_data:
            # Check for both original case and lowercase in environment variables
            env_key = (
                config_key.upper()
            )  # Convert to uppercase for environment variable check
            if env_key in os.environ:
                self.env[config_key] = os.environ[env_key]
