#!/usr/bin/env python3
import os
from core.env import EnvManager
from core.config_loader import ConfigLoader
from core.initializer import Initializer

if os.getenv("LOOPY_DEBUG") == "1":
    import debugpy

    debugpy.listen(("0.0.0.0", 5678))
    print("Waiting for debugger attach...")
    debugpy.wait_for_client()

# 1. Setup environment variabls
envManager = EnvManager()
config_path = envManager.get_config_path()
root_path = envManager.get_root_path()

# 2. Load config
config_loader = ConfigLoader(config_path, root_path)
config_loader.load()
config_data = config_loader.get_config()
default_vars = config_loader.get_default_vars()

# Update env_list with environment variables if they exist
envManager.update_env_from_system_if_config_key_exists(config_data)
env_list = envManager.get_env()

# 3. initializer
initializer = Initializer(env_list, config_data, default_vars)
loopy_context = initializer.initialize()

# import cli after initializer
from cli.cli import cli

if __name__ == "__main__":
    cli(obj=loopy_context)
