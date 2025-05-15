import yaml
import os

internal_config_path = "src/core/internal_config.yaml"


class ConfigLoader:
    def __init__(self, config_path: str, loopy_root_path: str = ""):
        self.config_path = config_path
        self.loopy_root_path = loopy_root_path
        self.internal_config_path = os.path.join(
            self.loopy_root_path, internal_config_path
        )
        self.config_data = {}
        self.default_vars = {}

    def load(self):
        self._load_config()
        self._load_default_vars()

    def _load_config(self):
        with open(self.config_path, "r") as file:
            config_data = yaml.safe_load(file)

        with open(self.internal_config_path, "r") as file:
            internal_conf_data = yaml.safe_load(file) or {}

        for key, value in internal_conf_data.items():
            if isinstance(value, dict):
                internal_conf_data[key] = {
                    k: self._add_prefix(v) for k, v in value.items()
                }
            else:
                internal_conf_data[key] = self._add_prefix(value)

        self.config_data = {**internal_conf_data, **config_data}

    def _load_default_vars(self):
        default_vars_path = self.config_data.get("default_vars_file")
        if not default_vars_path:
            raise ValueError("default_vars_file not found in config")

        if self.loopy_root_path:
            default_vars_path = os.path.join(self.loopy_root_path, default_vars_path)

        with open(default_vars_path, "r") as file:
            self.default_vars = yaml.safe_load(file)

    def get_config(self):
        return self.config_data

    def get_default_vars(self):
        return self.default_vars

    def _add_prefix(self, value):
        if isinstance(value, str) and not os.path.isabs(value):
            return os.path.join(self.loopy_root_path, value)
        return value
