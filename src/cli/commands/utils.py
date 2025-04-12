import os
import sys
import yaml
import logging
import click
from colorama import Fore

from commons.python.py_utils import is_positive
from core.context import get_context

context = get_context()
loopy_root_path = context["config"]["loopy_root_path"]
role_list = context["config"]["role_list"]
unit_list = context["config"]["unit_list"]
playbook_list = context["config"]["playbook_list"]

logger = logging.getLogger(__name__)

ROLE_SCHEMA_FILE_PATH = context["config"]["schema"]["role"]
UNIT_SCHEMA_FILE_PATH = context["config"]["schema"]["unit"]
PLAYBOOK_SCHEMA_FILE_PATH = context["config"]["schema"]["playbook"]


import logging.config


def verify_param_in_component(clickctx, params, component_name, component_list, component_type="component"):
    """
    Check if the given parameters exist in the specified component (role/unit/playbook).

    :param params: List of parameters to check
    :param component_name: The name of the component (role, unit, or playbook)
    :param component_list: The list of components to search through
    :param component_type: Type of the component (role, unit, playbook)
    """
    if not params:
        return

    input_exist = False
    target_param = None

    # Find the component (role, unit, or playbook) from the list
    for component in component_list:
        if component_name == component["name"]:
            component_config_path = component["path"] + "/config.yaml"
            with open(component_config_path, "r") as file:
                component_vars = yaml.safe_load(file)

                # Depending on the component type, check for parameters
                if component_type == "role":
                    input_exist = check_input_env_in_role(params, component_vars["role"]["input_env"])
                elif component_type == "unit":
                    role_name = component_vars["unit"]["steps"][0]["role"]["name"]
                    role_config_data = get_config_data_by_name(clickctx, role_name, "role", context["config"]["role_list"])
                    input_exist = check_input_env_in_role(params, role_config_data["role"]["input_env"])
                elif component_type == "playbook":
                    first_comp_info = component_vars["playbook"]["steps"][0]
                    first_comp_type = list(first_comp_info.keys())[0]
                    if first_comp_type == "role":
                        input_exist = check_input_env_in_role(params, first_comp_info["role"]["name"])
                    elif first_comp_type == "unit":
                        unit_name = first_comp_info["unit"]["name"]
                        input_exist = verify_param_in_component(clickctx, params, unit_name, component_list, "unit")

                if input_exist:
                    return

    # If input does not exist, log the error and exit
    target_param = list(params.keys())[0] if params else None
    logger.error(f"no input environment name exist: {target_param}")
    exit(1)


def check_input_env_in_role(params, role_input_env):
    """
    Helper function to check if the parameters exist in the given role's input environment.

    :param params: List of parameters to check
    :param role_input_env: The role's input environment to search in
    :return: Boolean indicating whether the input exists
    """
    ignore_validate_input_env = context["config"]["ignore_validate_input_env"]
    if ignore_validate_input_env:
        return True

    input_exist = False
    for param in params:
        for role_config_env in role_input_env:
            if str.lower(role_config_env["name"]) == str.lower(param):
                input_exist = True
                break
    return input_exist


def configure_logging(context, verbose=2):
    logging_config = context["config"]["logging"]
    default_log_level = logging_config["handlers"]["console"]["level"]

    log_levels = {1: logging.WARN, 2: logging.INFO, 3: logging.DEBUG}

    logging_config["handlers"]["console"]["level"] = log_levels.get(verbose, default_log_level)
    logging.config.dictConfig(logging_config)
    return logging_config["handlers"]["console"]["level"]


def verify_component_exist(component_name, component_list, component_type="component"):
    """
    Check if a component exists in the provided list.

    :param component_name: Name of the component to search for.
    :param component_list: List of components to search through.
    :param component_type: Type of the component (for error message formatting).
    """
    for component in component_list:
        if component_name == component["name"]:
            return
    logger.error(f"{component_type.title()} name({component_name}) does not exist")
    exit(1)


def get_default_vars(ctx):
    # return ctx.obj.get("config", "default_vars")["default_vars"]
    return context["default_vars"]


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
                    if not line.strip() or line.startswith("#"):  # Skip # part
                        continue
                    key, value = line.strip().split("=")
                    if '"' in value:
                        additional_vars[key] = value.replace('"', "")
                    else:
                        additional_vars[key] = value
        else:
            logger.error(f"File({file}) does not exist")
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
    path = ""
    if type == "unit":
        for unit in list:
            if name == unit["name"]:
                path = unit["path"]
                break
    else:
        for role in list:
            if name == role["name"]:
                path = role["path"]
                break
    if path == "":
        ctx.invoke(click.echo, f"{Fore.RED}Component({type})-{name} does not found.{Fore.RESET}")
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

def getDescription(clickCtx, component_name, component_type, parent_description=""):
    description = ""

    if component_type == "role":
        if parent_description !="":
            description = parent_description
        else: 
            role_config_data = get_config_data_by_name(clickCtx, component_name, "role", role_list)
            if "description" in role_config_data["role"]:
                description = role_config_data["role"]["description"]                    
        
    elif component_type == "unit":
        unit_config_data = get_config_data_by_name(clickCtx, component_name, "unit", unit_list)
        if "description" in unit_config_data["unit"]:
            description = unit_config_data["unit"]["description"]
    elif component_type == "playbook":
        playbook_config_data = get_config_data_by_name(clickCtx, component_name, "playbook", playbook_list)
        if "description" in playbook_config_data["playbook"]:
            description = playbook_config_data["playbook"]["description"]

    return description

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
        print(f"{result}{Fore.RESET}")
