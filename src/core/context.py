_global_context = {}


class LoopyContextBuilder:
    def __init__(self, env_list: dict, default_vars: dict, config_data: dict):
        self.default_vars = default_vars
        self.config_data = config_data
        self.env_list = env_list

    def build(self):
        global _global_context

        _global_context = {
            "default_vars": self.default_vars,
            "config": self.config_data,
            "env": self.env_list
        }

        return _global_context


def set_context(ctx: dict):
    global _global_context
    _global_context = ctx


def get_context() -> dict:
    return _global_context


def get_schema_path(schema_type: str) -> str:
    return _global_context.get("schema_paths", {}).get(schema_type, "")


def update_config_data(key: str, value):
    if "_global_context" not in globals():
        raise RuntimeError("Global context has not been initialized yet.")

    config = _global_context.get("config", {})
    config[key] = value
