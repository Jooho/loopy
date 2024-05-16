import os
import sys
import yaml
import re
import click
from jsonschema import Draft7Validator
from colorama import Fore, Style
from prettytable import PrettyTable

loopy_root_path = os.environ.get("LOOPY_PATH", "")

ROLE_SCHEMA_FILE_PATH = "./src/schema/role.yaml"
UNIT_SCHEMA_FILE_PATH = "./src/schema/unit.yaml"
PLAYBOOK_SCHEMA_FILE_PATH = "./src/schema/playbook.yaml"

if loopy_root_path:
    ROLE_SCHEMA_FILE_PATH = f"{loopy_root_path}/src/schema/role.yaml"
    UNIT_SCHEMA_FILE_PATH = f"{loopy_root_path}/src/schema/unit.yaml"
    PLAYBOOK_SCHEMA_FILE_PATH = f"{loopy_root_path}/src/schema/playbook.yaml"    

def initialize(directory, type):
    item_list = []

    for root, dirs, files in os.walk(directory):
        if "config.yaml" in files:
            config_path = os.path.join(root, "config.yaml")

            file_errors = validate_role_yaml(config_path, type)
            if file_errors:
                for error in file_errors:
                    print(f"{Fore.RED}YAML Schema Error!{Style.RESET_ALL}")
                    print(f"{Fore.RED}ERROR: {error}{Style.RESET_ALL}")
                    print(f"{Fore.BLUE}YAML Content({config_path}){Style.RESET_ALL}")
                    exit(1)

            with open(config_path, "r") as config_file:
                config_data = yaml.safe_load(config_file)

                if config_data:
                    if type == "unit":
                        path = os.path.abspath(root)
                        if "name" in config_data[type]:
                            name = config_data[type]["name"]
                        else:
                            name = convert_path_to_component_name(path, type)
                        if "steps" in config_data[type]:
                            role_name = config_data[type]["steps"][0]["role"]["name"]
                        else:
                            role_name = config_data[type]["role"]["name"]
                        item_list.append({"name": name, "path": path, "role_name": role_name})
                    else:
                        path = os.path.abspath(root)
                        if "name" in config_data[type]:
                            name = config_data[type]["name"]
                        else:
                            name = convert_path_to_component_name(path, type)
                        item_list.append({"name": name, "path": path})
    return item_list


def convert_path_to_component_name(path, component):
    pattern = r"/" + component + "s/(.*)/(.*)$"
    match = re.search(pattern, path + "/")
    if match:
        dir_names = match.group(1).split("/")
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
        if item.count("=") >= 2:
            value_str = str(item)
            first_eq_index = value_str.find("=")
            key = value_str[:first_eq_index]
            val = value_str[first_eq_index + 1 :]
            result[key] = val
        else:
            key, value = item.split("=")
            result[key] = value

    return result


def load_env_file_if_exist(file):
    additional_vars = {}
    if file is not None:
        if os.path.exists(file):
            with open(file, "r") as file:
                for line in file:
                    if not line or line.startswith("#"):  # Skip # part
                        continue
                    key, value = line.strip().split("=")
                    if '"' in value:
                        additional_vars[key] = value.replace('"', "")
                    else:
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


def get_config_data_by_config_file_dir(ctx, config_file_dir):
    try:
        with open(os.path.join(config_file_dir, "config.yaml"), "r") as config_file:
            config_data = yaml.safe_load(config_file)
            return config_data
    except FileNotFoundError:
        ctx.invoke(click.echo(f"Config file '{config_file_dir}/config.yaml' not found."))


def get_config_data_by_name(ctx, name, type, list):
    path=""    
    if type == "unit":
        for unit in list:
            if name == unit["name"]:
                path = unit["path"]
    else:
        for role in list:
            if name == role["name"]:
                path = role["path"]
    if path == "":
        ctx.invoke(click.echo,f"{Fore.RED}Component({type})-{name} does not found.{Fore.RESET}") 
        sys.exit(1)
    return get_config_data_by_config_file_dir(ctx, path)


def get_input_env_from_config_data(role_config_data):
    if "input_env" not in role_config_data:
        return None
    else:
        return role_config_data["input_env"]


def get_input_env_from_unit_config_data(unit_config_data):
    if "input_env" not in unit_config_data:
        return None
    else:
        return unit_config_data["input_env"]


def get_first_role_name_in_unit_by_unit_name(unit_name, list):
    for unit in list:
        if unit_name == unit["name"]:
            return unit["role_name"]


def validate_role_yaml(yaml_file, type):
    schema = None
    schema_file_path = None
    # Load schema file
    if type == "role":
        schema_file_path = ROLE_SCHEMA_FILE_PATH
    elif type == "unit":
        schema_file_path = UNIT_SCHEMA_FILE_PATH
    elif type == "playbook":
        schema_file_path = PLAYBOOK_SCHEMA_FILE_PATH

    with open(schema_file_path, "r") as schema_file:
        schema = yaml.safe_load(schema_file)

    # Load Target yaml file
    try:
        with open(yaml_file, "r") as f:
            yaml_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"{Fore.RED}YAML File Syntax Error:{Style.RESET_ALL}", e)
        exit(1)

    # Create validator
    validator = Draft7Validator(schema)

    # Validate YAML Data
    errors = []
    for error in validator.iter_errors(yaml_data):
        errors.append({"message": error.message, "path": list(error.path)})
    return errors


def print_logo():
    print("")

    text = [
        r"__/\\\____________________/\\\\\_____________/\\\\\________/\\\\\\\\\\\\\_____/\\\________/\\\_",
        r" _\/\\\__________________/\\\///\\\_________/\\\///\\\_____\/\\\/////////\\\__\///\\\____/\\\/__",
        r"  _\/\\\________________/\\\/__\///\\\_____/\\\/__\///\\\___\/\\\_______\/\\\____\///\\\/\\\/____",
        r"   _\/\\\_______________/\\\______\//\\\___/\\\______\//\\\__\/\\\\\\\\\\\\\/_______\///\\\/______",
        r"    _\/\\\______________\/\\\_______\/\\\__\/\\\_______\/\\\__\/\\\/////////___________\/\\\_______",
        r"     _\/\\\______________\//\\\______/\\\___\//\\\______/\\\___\/\\\____________________\/\\\_______",
        r"      _\/\\\_______________\///\\\__/\\\______\///\\\__/\\\_____\/\\\____________________\/\\\_______",
        r"       _\/\\\\\\\\\\\\\\\_____\///\\\\\/_________\///\\\\\/______\/\\\____________________\/\\\_______",
        r"        _\///////////////________\/////_____________\/////________\///_____________________\///________",
    ]

    for line in text:
        result = ""
        is_red = False
        for i, char in enumerate(line):
            if char != "_" and is_red == False:
                is_red = True
                result += Fore.RED + char
            elif char != "_" and is_red == True:
                result += char
            elif char == "_" and is_red == True:
                is_red = False
                result += Fore.BLUE + char
            elif char == "_" and is_red == False:
                result += Fore.BLUE + char
            else:
                result += char
        print(result)
