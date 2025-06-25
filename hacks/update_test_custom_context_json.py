#!/usr/bin/env python
import yaml
import json
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))  
src_path = os.path.join(root_dir, "src")

if src_path not in sys.path:
    sys.path.insert(0, src_path)

from core.initializer import Initializer
from core.env import EnvManager
from core.config_loader import ConfigLoader
from core.context import LoopyContext

def main():
    os.environ["LOOPY_ROOT_PATH"] = f"{root_dir}"
    envManager = EnvManager()
    config_path = envManager.get_config_path()
    root_path = envManager.get_root_path()
    env_list = envManager.get_env()

    config_loader = ConfigLoader(config_path, root_path)
    config_loader.load()
    config_data = config_loader.get_config()
    default_vars = config_loader.get_default_vars()
    
    # Set test role/unit/playbook path
    config_data["additional_role_dirs"] = [f"{root_dir}/tests/test-data/roles"]
    config_data["additional_unit_dirs"] = [f"{root_dir}/tests/test-data/units"]
    config_data["additional_playbook_dirs"] = [f"{root_dir}/tests/test-data/playbooks"]
    
    initializer = Initializer(env_list, config_data, default_vars)
    ctx_object = initializer.initialize()

    with open(f"{root_dir}/tests/custom-context.json", "w") as f:
        json.dump(ctx_object, f, indent=4)

if __name__ == "__main__":
    main()
