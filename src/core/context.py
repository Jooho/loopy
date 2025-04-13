_global_context = {}


class LoopyContextBuilder:
    def __init__(self, env_list: dict, default_vars: dict, config_data: dict):
        self.default_vars = default_vars
        self.config_data = config_data
        self.env_list = env_list

    def build(self):
        global _global_context

        _global_context = {"default_vars": self.default_vars, "config": self.config_data, "env": self.env_list}

        return _global_context


def set_context(ctx: dict):
    global _global_context
    _global_context = ctx


def get_context() -> dict:
    return _global_context


def update_config_data(key: str, value):
    if "_global_context" not in globals():
        raise RuntimeError("Global context has not been initialized yet.")

    config = _global_context.get("config", {})
    config[key] = value


from typing import Any, Dict, List, Optional


class LoopyContext:
    def __init__(self, raw_obj: Dict[str, Any]):
        config = raw_obj.get("config", {})
        default_vars = raw_obj.get("default_vars", {})
        self.config: Dict = config
        self.default_vars: Dict = default_vars
        self.loopy_root_path: Optional[str] = config.get("loopy_root_path")
        self.role_list: List[str] = config.get("role_list", [])
        self.unit_list: List[str] = config.get("unit_list", [])
        self.playbook_list: List[str] = config.get("playbook_list", [])
        self.logging: Dict = config.get("logging", {})
        self.loopy_result_dir: str = config.get("loopy_result_dir", "")

        self.debug: bool = config.get("debug", False)

    def __repr__(self):
        return (
            f"LoopyContext("
            f"config={self.config}, "
            f"default_vars={self.default_vars}, "
            f"logging={self.logging}, "
            f"loopy_result_dir={self.loopy_result_dir}, "
            f"loopy_root_path={self.loopy_root_path}, "
            f"role_list={self.role_list}, "
            f"unit_list={self.unit_list}, "
            f"playbook_list={self.playbook_list}, "
            f"debug={self.debug})"
        )
