import os
import yaml
import re
import click
from jsonschema import Draft7Validator
from colorama import Fore, Style
from config import summary_dict, load_summary
from prettytable import PrettyTable


ROLE_SCHEMA_FILE_PATH = "./src/schema/role.yaml"
UNIT_SCHEMA_FILE_PATH = "./src/schema/unit.yaml"
PLAYBOOK_SCHEMA_FILE_PATH = "./src/schema/playbook.yaml"


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
    if type == "unit":
        for unit in list:
            if name == unit["name"]:
                path = unit["path"]
    else:
        for role in list:
            if name == role["name"]:
                path = role["path"]
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


def summary(ctx, type, config_data, unit_list):
    load_summary()
    summary_text = ["╦  ╔═╗╔═╗╔═╗╦ ╦", "║  ║ ║║ ║╠═╝╚╦╝", "╩═╝╚═╝╚═╝╩   ╩ ", "╔═╗┬ ┬┌┬┐┌┬┐┌─┐┬─┐┬ ┬", "╚═╗│ │││││││├─┤├┬┘└┬┘", "╚═╝└─┘┴ ┴┴ ┴┴ ┴┴└─ ┴ "]
    first_component_type = summary_dict["first_component_type"]
    first_component_name = summary_dict["first_component_name"]
    loopy_result_dir = summary_dict["loopy_result_dir"]
    start_time = summary_dict["start_time"]
    end_time = summary_dict["end_time"]

    execution_time = end_time[-1] - start_time[0]
    total_minutes = int(execution_time // 60)
    total_seconds = round(float(execution_time % 60), 2)

    additional_info = [
        f"Run: {first_component_type}({first_component_name})",
        f"Loopy result dir: {loopy_result_dir}",
        f"Report file: {loopy_result_dir}/report",
        f"Execution time: {total_minutes}min {total_seconds}secs",
    ]

    # Find the maximum length of text lines
    max_line_length = max(len(line) for line in summary_text) + 100

    # Print top border
    print("*" * (max_line_length + 4))

    # Print text with *
    for line in summary_text:
        padding_length = (max_line_length - len(line)) // 2
        print("* " + " " * padding_length + line + " " * (max_line_length - len(line) - padding_length) + " *")
    # Print additional info
    for info in additional_info:
        padding_length = (max_line_length - len(info)) // 2
        key = info.split(":")[0].strip()
        value = info.split(":")[1].strip()
        new_string = f"{Fore.BLUE}{key}{Fore.RESET}" + ":" + f"{Fore.YELLOW} {value}{Fore.RESET}"

        print("* " + " " * padding_length + new_string + " " * (max_line_length - len(info) - padding_length) + " *")

    # Print bottom border
    print("*" * (max_line_length + 4))

    # Report Table
    report_file = os.path.join(summary_dict["loopy_result_dir"], "report")

    # Execution time per role
    execution_time_min_list = [int((end - start) // 60) for start, end in zip(start_time, end_time)]
    execution_time_sec_list = [round(float((end - start) % 60), 2) for start, end in zip(start_time, end_time)]

    table = PrettyTable(["Index", "Role Name", "Result", "Time", "Folder"])
    with open(f"{report_file}", "r") as file:
        data = file.readlines()
        prev_index = None
        prev_sub_index = 0
        prev_role_name = None
        final_index = None
        sub_index = 0
        exec_min_time = 0.0
        exec_sec_time = 0.0
        for line in data:
            line = line.strip()  # Delete enter
            if not line or line.startswith("#"):  # Skip # part
                continue
            if summary_dict["first_component_type"] == "Role":  # Role run does not have index in the report.
                if prev_index is None:
                    index = "0"
                    report_data = line
                else:
                    sub_index = sub_index + 1
            else:
                if "-" in line:
                    index, report_data = line.split("-", 1)
            result_data = report_data.split("::")  # separate data by "::""
            role_name = result_data[0]
            result = result_data[-1]

            if prev_index == index and prev_role_name == role_name:
                sub_index = prev_sub_index + 1
                final_index = f"{index}-{sub_index}"
                prev_sub_index = prev_sub_index + 1
                exec_min_time = execution_time_min_list[sub_index]
                exec_sec_time = execution_time_sec_list[sub_index]
            else:
                final_index = index
                prev_index = index
                prev_role_name = role_name
                prev_sub_index = 0
                sub_index = 0
                exec_min_time = execution_time_min_list[int(index)]
                exec_sec_time = execution_time_sec_list[int(index)]

            description = ""
            if type == "unit":
                steps = config_data[type]["steps"]
                if "description" in steps[int(index)]["role"]:
                    description = steps[int(index)]["role"]["description"]
            if type == "playbook":
                description = getDescription(ctx, role_name, int(index), config_data, unit_list)
                
            table.add_row(
                [
                    final_index.strip(),
                    description if description != "" else role_name.strip(),
                    f"{Fore.GREEN}Success{Fore.RESET}" if result.strip() == "0" else f"{Fore.RED}Fail{Fore.RESET}",
                    f"{exec_min_time}min {exec_sec_time}sec",
                    os.path.join(loopy_result_dir, "artifacts", index + "-" + role_name),
                ]
            )

        print(table)

def getDescription(ctx, role_name, index, py_config_data, unit_list):
    description = ""
    steps = py_config_data["playbook"]["steps"]

    for step_index, step in enumerate(steps):
        if "unit" in step:
            unit_name = step["unit"]["name"]
            unit_config_data = get_config_data_by_name(ctx, unit_name, type, unit_list)
            for role in unit_config_data["unit"]["steps"]:
                if role["role"]["name"] == role_name:
                    role = role["role"]
                    if "description" in role:
                        description = role["description"]
                        break
        else:
            if step["role"]["name"] == role_name and index == step_index:
                if "description" in step["role"]:
                    description = step["role"]["description"]
                    break
    return description
