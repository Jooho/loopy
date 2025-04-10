#!/usr/bin/env python3
from core.env import EnvManager
from core.config_loader import ConfigLoader
from core.initializer import Initializer
from core.context import get_context

# 1. Setup environment variabls
envManager = EnvManager()
config_path = envManager.get_config_path()
root_path = envManager.get_root_path()
env_list = envManager.get_env()

# 2. Load config
config_loader = ConfigLoader(config_path, root_path)
config_loader.load()
config_data = config_loader.get_config()
default_vars = config_loader.get_default_vars()

# 3. initializer
initializer = Initializer(env_list, config_data, default_vars)
initializer.initialize()

# import cli after initializer
from cli.cli import cli

# 4. CLI execution
global_context = get_context()

if __name__ == "__main__":
    cli(obj=global_context)
