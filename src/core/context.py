class LoopyContextBuilder:
    def __init__(self, default_vars: dict, config_data: dict):
        self.default_vars = default_vars
        self.config_data = config_data

    def build(self):
        return {
            "config": {
                "default_vars": self.default_vars,
                "config_data": self.config_data,
            }
        }
