#!/usr/bin/env python
import yaml
import json
import os

def find_root_directory(cur_dir):
    while not os.path.isdir(os.path.join(cur_dir, ".git")) and cur_dir != "/":
        cur_dir = os.path.dirname(cur_dir)
    if os.path.isdir(os.path.join(cur_dir, ".git")):
        return cur_dir
    else:
        return None

current_dir = os.path.dirname(os.path.abspath(__file__))
root_directory = find_root_directory(current_dir)

def load_configs(config_file, default_vars_file):
    with open(config_file, "r") as f:
        config_data = yaml.safe_load(f)
    
    with open(default_vars_file, "r") as f:
        default_vars = yaml.safe_load(f)

    return config_data, default_vars

def merge_configs(config_data, default_vars_data):
    merged_json={}
    config={}
    config["config_data"] = config_data
    config["default_vars"] = default_vars_data
    merged_json["config"]=config
    return merged_json

def main():
    config_file = f"{root_directory}/config.yaml"
    default_vars_file = f"{root_directory}/commons/default-variables.yaml"

    config_data, default_vars_data = load_configs(config_file, default_vars_file)
    json_data = merge_configs(config_data, default_vars_data)
    with open(f"{root_directory}/tests/custom-context.json", "w") as f:
        json.dump(json_data, f, indent=4)

if __name__ == "__main__":
    main()
