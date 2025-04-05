# core/config_loader.py

import yaml
import os


class ConfigLoader:
    def __init__(self, config_path: str, root_path: str = ""):
        self.config_path = config_path
        self.root_path = root_path
        self.config_data = {}
        self.default_vars = {}

    def load(self):
        self._load_config()
        self._load_default_vars()

    def _load_config(self):
        with open(self.config_path, "r") as file:
            self.config_data = yaml.safe_load(file)

    def _load_default_vars(self):
        default_vars_path = self.config_data.get("default_vars_file")
        if not default_vars_path:
            raise ValueError("default_vars_file not found in config")

        if self.root_path:
            default_vars_path = os.path.join(self.root_path, default_vars_path)

        with open(default_vars_path, "r") as file:
            self.default_vars = yaml.safe_load(file)

    def get_config(self):
        return self.config_data

    def get_default_vars(self):
        return self.default_vars
