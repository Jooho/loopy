import os
import sys
from core.context import set_context


class EnvManager:
    def __init__(self):
        self.loopy_root_path = os.environ.get("LOOPY_PATH", "")
        self.loopy_config_name = os.environ.get(
            "LOOPY_CONFIG_NAME", "config.yaml")
        self.loopy_config_path =  os.path.join(
                self.loopy_root_path, self.loopy_config_name)
        
        self.current_dir = self.loopy_root_path or os.path.dirname(
            os.path.abspath(__file__))
        if not self.loopy_root_path:
            self.loopy_root_path = os.path.abspath(
                os.path.join(self.current_dir, "..", ".."))
        self.commands_dir = os.path.join(
            self.loopy_root_path, "src", "cli", "commands")
        self.cli_dir = os.path.join(self.loopy_root_path, "src", "cli")
        self.logics_dir = os.path.join(
            self.loopy_root_path, "src", "cli", "logics")
        self.py_utils_dir = os.path.join(
            self.loopy_root_path, "commons", "python")

        self.setup_sys_paths()        

    def setup_sys_paths(self):
        sys.path.append(self.commands_dir)
        sys.path.append(self.cli_dir)
        sys.path.append(self.logics_dir)
        sys.path.append(self.py_utils_dir)

    def get_config_path(self):
        return self.loopy_config_path

    def get_root_path(self):
        return self.loopy_root_path

    def get_env(self):
        env = {
            "loopy_root_path": self.loopy_root_path,
            "loopy_config_path": self.loopy_config_path,
            "loopy_config_name": self.loopy_config_name,
            "commands_dir": self.commands_dir,
            "cli_dir": self.cli_dir,
            "logics_dir": self.logics_dir,
            "py_utils_dir": self.py_utils_dir,
        }
        return env        