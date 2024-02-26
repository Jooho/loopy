import os
import yaml
import re


def initialize(directory, type):
    item_list = []

    for root, dirs, files in os.walk(directory):
        if "config.yaml" in files:
            config_path = os.path.join(root, "config.yaml")
            with open(config_path, "r") as config_file:
                config_data = yaml.safe_load(config_file)
                if config_data:                                        
                    if type == "unit":
                        path = os.path.abspath(root)
                        if 'name' in config_data[type]:
                            name = config_data[type]["name"]
                        else:
                            name = convert_path_to_component_name(path,type)
                        role_name = config_data[type]["role"]["name"]
                        item_list.append({"name": name, "path": path, "role_name": role_name})
                    else:
                        path = os.path.abspath(root)
                        if 'name' in config_data[type]:
                            name = config_data[type]["name"]
                        else:
                            name = convert_path_to_component_name(path,type)
                        item_list.append({"name": name, "path": path})
    return item_list


def convert_path_to_component_name(path, component):
    print(path)
    pattern = r"/" + component + "s/(.*)/(.*)$"
    print(pattern)
    match = re.search(pattern, path + "/")
    print(match)
    if match:
        dir_names = match.group(1).split("/")
        print(dir_names)
        component_name = "-".join(dir_names)
        return f"{component_name}"
    else:
        return None


def get_default_vars(ctx):
    return ctx.obj.get("config", "default_vars")["default_vars"]


def parse_key_value_pairs(ctx, param, value):
    if value is None:
        return {}

    result = {}
    for item in value:
        key, value = item.split("=")
        result[key] = value

    return result


def load_env_file_if_exist(file):
    additional_vars = {}
    if file is not None:
        if os.path.exists(file):
            with open(file, "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    # os.environ[key] = value
                    additional_vars[key] = value
        else:
            print(f"File({file}) does not exist")
            exit(1)
    return additional_vars


def set_env_vars_if_file_exist(file):
    if file is not None:
        if os.path.exists(file):
            with open(file, "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    os.environ[key] = value


def update_params_with_input_file(additional_vars_from_file, params):
    updated_params = params
    if len(additional_vars_from_file) != 0:
        for key, value in params.items():
            additional_vars_from_file[key] = value
        updated_params = additional_vars_from_file
    return updated_params
