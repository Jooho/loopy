import os
import sys


class EnvManager:

    def __init__(self):
        self.env = self.add_loopy_env_vars()

        if not self.env.get("loopy_root_path"):
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.loopy_root_path = os.path.abspath(os.path.join(current_dir, "..", ".."))
            self.env["loopy_root_path"] = self.loopy_root_path

        if not self.env.get("loopy_config_name"):
            self.loopy_config_name = os.environ.get("LOOPY_CONFIG_NAME", "config.yaml")
            self.env["loopy_config_name"] = self.loopy_config_name

        self.loopy_root_path = self.env["loopy_root_path"]
        self.loopy_config_name = self.env["loopy_config_name"]
        self.loopy_config_path = os.path.join(self.loopy_root_path, self.loopy_config_name)
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
                env[key.lower()] = value
        return env

    def get_config_path(self):
        return self.loopy_config_path

    def get_root_path(self):
        return self.loopy_root_path

    def get_env(self):
        return self.env
