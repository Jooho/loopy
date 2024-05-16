#!/usr/bin/env python
import yaml
import json

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
    config_file = "config.yaml"
    default_vars_file = "commons/default-variables.yaml"

    config_data, default_vars_data = load_configs(config_file, default_vars_file)
    json_data = merge_configs(config_data, default_vars_data)
    with open("./tests/custom-context.json", "w") as f:
        json.dump(json_data, f, indent=4)

if __name__ == "__main__":
    main()
