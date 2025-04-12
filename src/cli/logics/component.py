import subprocess
import os
import yaml
import uuid
import datetime
from cli.commands import utils
from cli.commands import constants

import time
import logging
from core.report_manager import LoopyReportManager
from colorama import Fore, Style, Back
from core.context import get_context, update_config_data

context = get_context()
config_dict = context["config"]
role_list = context["config"]["role_list"]
unit_list = context["config"]["unit_list"]
playbook_list = context["config"]["playbook_list"]
# Update config.json
reportManager = LoopyReportManager(config_dict["loopy_root_path"])
first_component_type = None
first_component_name = None

logger = logging.getLogger(__name__)


class Role:
    def __init__(self, clickCtx, index, role_list, role_name, role_description, params, param_output_env_file, additional_input_vars=None):
        self.index = index
        self.name = role_name
        self.role_description = role_description
        self.role_config_dir_path = get_role_config_dir_path(role_list, role_name)
        self.params = params
        self.clickCtx = clickCtx
        self.param_output_env_file = param_output_env_file
        self.additional_input_vars = additional_input_vars

        self.uuid = str(uuid.uuid4())  # unique id
        self.start_time = None
        self.end_time = None
        self.execution_time = 0  # sec

    def start(self):
        logger.info(f"{Back.BLUE}Start Role '{self.name}' {Fore.RESET}")
        global first_component_type, first_component_name
        enable_loopy_log = utils.is_positive(config_dict["enable_loopy_log"])
        output_env_dir_path = config_dict["output_dir"]
        artifacts_dir_path = config_dict["artifacts_dir"]
        report_file = config_dict["report_file"]
        loopy_result_dir = config_dict["loopy_result_dir"]

        # Setup for role
        if first_component_type is None:
            first_component_type = "Role"
            first_component_name = self.name
            self.index = 0
            reportManager.update_summary("first_component_type", "Role")
            reportManager.update_summary("first_component_name", self.name)
            role_dir_path = os.path.join(artifacts_dir_path, self.name)
        else:
            role_dir_name = f"{self.index}-{self.name}"
            role_dir_path = os.path.join(artifacts_dir_path, role_dir_name)

        logger.info(f"{Fore.LIGHTBLUE_EX}Role '{self.name}': Gathering environment and setting environment variables{Fore.RESET}")

        ## Create output dir
        create_dir_or_file_if_does_not_exist(output_env_dir_path)
        create_dir_or_file_if_does_not_exist(report_file, fileType=True)
        reportManager.update_summary("loopy_result_dir", loopy_result_dir)

        ## Create artifacts dir
        create_dir_or_file_if_does_not_exist(role_dir_path)
        ## This is for ROLE_DIR in role main.sh/main.py
        os.environ["REPORT_FILE"] = report_file
        os.environ["ROLE_DIR"] = role_dir_path
        update_config_data("role_dir", role_dir_path)
        log_output_file = os.path.join(role_dir_path, "log")
        output_env_file_full_path = get_output_env_file_path(self.index, output_env_dir_path, self.role_config_dir_path, self.param_output_env_file)
        os.environ["OUTPUT_ENV_FILE"] = output_env_file_full_path

        # Validate input/output variables
        ## Gather all input variables
        aggregated_input_vars, required_envs = get_aggregated_input_vars(self.clickCtx, self.role_config_dir_path, self.name, self.params, self.additional_input_vars)

        ## Export the input variabels (This is main.sh/main.py)
        export_env_variables(self.clickCtx, aggregated_input_vars)

        ## Check if all required environment variables are set
        ## If not, raise an error
        verify_required_env_exist(required_envs)

        ## validate env_file path
        validate_and_cleanup_folder(output_env_file_full_path, context_name=f"Role '{self.name}'")

        # Initialize role_time
        reportManager.reset_role_time()
        start_time = reportManager.role_time_dict["start_time"]
        if self.name != "shell-execute":
            start_time.append(time.time())
            reportManager.update_role_time("start_time", start_time)

        # Execute the main script
        logger.info(f"{Fore.LIGHTBLUE_EX}Role '{self.name}': Executing script{Fore.RESET}")

        try:
            target_main_file_type = "bash"
            target_main_file = os.path.join(self.role_config_dir_path, "main.sh")
            if not os.path.exists(target_main_file):
                target_main_file = os.path.join(self.role_config_dir_path, "main.py")
                target_main_file_type = "python"

            if enable_loopy_log == 0:
                logger.info(f"{Fore.LIGHTBLUE_EX}------------------- ROLE Log Start-------------------{Fore.RESET}")
                # This show logs and also save it to file
                env = os.environ.copy()
                env["PYTHONUNBUFFERED"] = "1"

                # shell_isolate= utils.is_positive(os.getenv("SHELL_ISOLATE"))
                # shell_isolate=True
                try:
                    with open(log_output_file, "w") as f:
                        # with subprocess.Popen([target_main_file_type, target_main_file], stdout=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True, close_fds=True) as proc:
                        with subprocess.Popen(
                            [target_main_file_type, target_main_file],
                            stderr=subprocess.STDOUT,
                            stdout=subprocess.PIPE,
                            text=True,
                            bufsize=1,
                            universal_newlines=True,
                            close_fds=True,
                            env=env,
                        ) as proc:
                            for line in proc.stdout:
                                print(line, end="")
                                # sys.stdout.flush()
                                f.write(line)
                                f.flush()

                        # wait for a process
                        proc.wait()

                        # error check
                        if proc.returncode != 0:
                            # print(f"Error occurred while executing. Return code: {proc.returncode}")
                            logger.error(f"{Fore.RED}Error occurred while executing. Return code: {proc.returncode} {Fore.RESET}")
                except Exception as e:
                    # print(f"subprocess failed to execute role: {e}")
                    logger.error(f"{Fore.RED}subprocess failed to execute role: {e} {Fore.RESET}")

            else:
                # # TO-DO This does not show logs but save it to file
                with open(log_output_file, "w") as log_file:
                    proc = subprocess.run([target_main_file_type, target_main_file], capture_output=True, text=True, check=True)
                    log_file.write(proc.stdout)
                # print(proc.stdout.strip())

            # for stdout_line, stderr_line in zip(proc.stdout, proc.stderr):
            #     if stdout_line:
            #         print(stdout_line, end="")
            #         f.write(stdout_line)
            #     if stderr_line:
            #         print(stderr_line, end="")
            #         f.write(stderr_line)
        except subprocess.CalledProcessError as e:
            # print(f"{Fore.RED}Command failed with return code {e.returncode}:{Fore.RESET}")
            logger.error(f"{Fore.RED}Command failed with return code {e.returncode}:{Fore.RESET}")
            # print(e.output)
            logger.error(e.output)
        logger.info(f"{Fore.LIGHTBLUE_EX}------------------- ROLE Log End-------------------{Fore.RESET}")

        logger.info(f"{Fore.LIGHTBLUE_EX}Role '{self.name}': Validating output file with specific environment variables{Fore.RESET}")
        validate_output_env_file(output_env_file_full_path, self.role_config_dir_path)

        logger.info(f"{Fore.LIGHTBLUE_EX}Role '{self.name}': Releasing exported environment variables for this role{Fore.RESET}")
        release_exported_env_variables(self.clickCtx, aggregated_input_vars)

        logger.info(f"{Back.BLUE}Finished Role '{self.name}' {Fore.RESET}")
        print()
        print(f"{Fore.RESET}")

        # end time update
        reportManager.load_role_time()
        end_time = reportManager.role_time_dict["end_time"]

        if self.name != "shell-execute":
            end_time.append(time.time())
            reportManager.update_role_time("end_time", end_time)

        if first_component_type == "Role":
            reportManager.update_summary("components", get_role_result(self.clickCtx, self.name, self.uuid, self.index, self.role_description))
            return
        else:
            return get_role_result(self.clickCtx, self.name, self.uuid, self.index, self.role_description)


class Unit:

    def __init__(self, clickCtx, unit_name):
        self.clickCtx = clickCtx
        self.name = unit_name
        self.components = []
        self.role_result_components = []
        self.uuid = str(uuid.uuid4())  # unique id

    def add_component(self, role):
        self.components.append(role)

    def start(self):
        global first_component_type, first_component_name
        if first_component_type is None:
            first_component_type = "Unit"
            first_component_name = self.name
            reportManager.update_summary("first_component_type", "Unit")
            reportManager.update_summary("first_component_name", self.name)

        # print(f"{Fore.LIGHTCYAN_EX}Running unit '{self.name}': Starting role{Fore.RESET}")
        logger.info(f"{Fore.LIGHTCYAN_EX}Running unit '{self.name}': Starting role{Fore.RESET}")
        for component in self.components:
            role_result = component.start()
            self.role_result_components.append(role_result)
        if first_component_type == "Unit":
            reportManager.update_summary("components", add_unit_result(self.clickCtx, self.name, self.uuid, self.role_result_components))
        else:
            return add_unit_result(self.clickCtx, self.name, self.uuid, self.role_result_components)


class Playbook:
    def __init__(self, clickCtx, name):
        self.clickCtx = clickCtx
        self.name = name
        self.components = []
        self.result_components = []
        self.uuid = str(uuid.uuid4())  # unique id

    def add_component(self, component):
        self.components.append(component)

    def start(self):
        # print()
        global first_component_type, first_component_name
        if first_component_type is None:
            first_component_type = "Playbook"
            first_component_name = self.name
            reportManager.update_summary("first_component_type", "Playbook")
            reportManager.update_summary("first_component_name", self.name)

        # print(f"{Back.CYAN}Running Playbook '{self.name}': Starting components{Fore.RESET}")
        logger.info(f"{Back.CYAN}Running Playbook '{self.name}': Starting components{Fore.RESET}")
        for component in self.components:
            component_result = component.start()
            self.result_components.append(component_result)
        reportManager.update_summary("components", add_playbook_result(self.clickCtx, self.name, self.uuid, self.result_components))


def add_playbook_result(clickCtx, playbook_name, uuid, components_result):
    playbook_component = {
        "type": "playbook",
        "name": playbook_name,
        "description": utils.getDescription(clickCtx, playbook_name, "playbook"),
        "uuid": uuid,
        "components": components_result,
        "start_time": "",
        "end_time": "",
        "execution_time": 0,
        "result": 0,
    }

    playbook_start_time = components_result[0]["start_time"]
    playbook_end_time = components_result[-1]["end_time"]
    exec_time = playbook_end_time - playbook_start_time

    playbook_component["start_time"] = playbook_start_time
    playbook_component["end_time"] = playbook_end_time
    playbook_component["execution_time"] = round(exec_time, 3)

    return playbook_component


def add_unit_result(clickCtx, unit_name, uuid, role_result_components):
    unit_component = {
        "type": "unit",
        "name": unit_name,
        "description": utils.getDescription(clickCtx, unit_name, "unit"),
        "uuid": uuid,
        "components": role_result_components,
        "start_time": "",
        "end_time": "",
        "execution_time": 0,
        "result": 0,
    }

    unit_start_time = role_result_components[0]["start_time"]
    unit_end_time = role_result_components[-1]["end_time"]
    exec_time = unit_end_time - unit_start_time

    unit_component["start_time"] = unit_start_time
    unit_component["end_time"] = unit_end_time
    unit_component["execution_time"] = round(exec_time, 3)

    return unit_component


def get_role_result(clickCtx, role_name, uuid, role_index, role_description=""):
    role_component = {
        "type": "role",
        "name": role_name,
        "description": utils.getDescription(clickCtx, role_name, "role", role_description),
        "artifacts_dir": os.path.join(config_dict["artifacts_dir"], f"{role_index}-{role_name}"),
        "uuid": uuid,
        "role_index": role_index,
        "commands": [],
        "start_time": "",
        "end_time": "",
        "execution_time": 0,
        "result": 0,
    }

    start_time = reportManager.role_time_dict["start_time"]
    end_time = reportManager.role_time_dict["end_time"]
    for i in range(len(start_time)):
        start = start_time[i]
        end = end_time[i]
        exec_time = end - start
        role_component["commands"].append({"name": f"command-{i+1}", "start_time": start, "end_time": end, "execution_time": round(exec_time, 3), "result": 0})

    # Calculate role total execution time
    role_component["start_time"] = role_component["commands"][0]["start_time"]
    role_component["end_time"] = role_component["commands"][-1]["end_time"]
    role_component["execution_time"] = sum(cmd["execution_time"] for cmd in role_component["commands"])

    return role_component


def validate_and_cleanup_folder(path: str, context_name: str = ""):
    """
    Sanity check the folder path, and remove it if it exists and is not a root directory or empty.
    :param path: Full path to the folder
    :param context_name: Optional name for logging context
    """
    # Safety check: Raise an error if the file path is "/" or an empty path
    if path in ["/", ""]:
        raise ValueError("Root directory or an empty path cannot be used as a file path.")

    # Safety check: Raise an error if the path is a directory
    if os.path.isdir(path):
        raise IsADirectoryError(f"{path} is a directory, not a file.")

    # If the file exists, remove it
    if os.path.exists(path):
        os.remove(path)  # Use os.rmdir for empty directory removal
        logger.info(f"Removed existing file: {path} (Context: {context_name})")


def create_dir_or_file_if_does_not_exist(path, fileType=False):
    item_type = "file" if fileType else "directory"
    if not os.path.exists(path):
        try:
            if fileType:
                with open(path, "w") as file:
                    file.write("# This is created by loopy.\n")
            else:
                os.makedirs(path)
            logger.info(f"{Fore.GREEN}Succeed to create a new {item_type}: {path}{Fore.RESET}")
        except OSError as e:
            logger.error(f"{Fore.RED}Failed to create a new ${item_type}: {path} ({e}){Fore.RESET}")


def release_exported_env_variables(clickCtx, input_variabels):
    keep_env_variables = context["config"]["keep_env_variables"]
    # keep_env_variables = clickCtx.obj.get("config", "config_data")["config_data"]["keep_env_variables"]
    for input_var in input_variabels:
        if input_var not in keep_env_variables:
            os.environ.pop(input_var)

    # print(f"{Fore.GREEN} \u21B3 Successfully release exported input variables {Fore.RESET}")
    logger.info(f"{Fore.GREEN} \u21b3 Successfully release exported input variables {Fore.RESET}")


def export_env_variables(clickCtx, input_variabels):
    logger.debug(f"{Fore.YELLOW} Input Environmental Variables {Fore.RESET}")
    logger.debug(f"{Fore.LIGHTYELLOW_EX} \u21b3 {input_variabels} {Fore.RESET}")

    if "STOP_WHEN_FAILED" not in input_variabels:
        # Set default value of stop_when_failed when it is not specified in the role/unit input_env or params
        os.environ["STOP_WHEN_FAILED"] = config_dict["stop_when_failed"]

    for input_var in input_variabels:
        os.environ[input_var] = input_variabels[input_var]

    logger.info(f"{Fore.GREEN} \u21b3 Successfully export input variables {Fore.RESET}")


def Get_default_input_value(clickCtx, role_config_dir_path, role_name, additional_input_vars, input_key):
    aggregated_input_vars, _ = get_aggregated_input_vars(clickCtx, role_config_dir_path, role_name, None, additional_input_vars)

    if input_key in aggregated_input_vars:
        return aggregated_input_vars[input_key]

    return ""


def Get_required_input_keys(clickCtx, role_config_dir_path, role_name):
    _, required_envs = get_aggregated_input_vars(clickCtx, role_config_dir_path, role_name, None, None)

    return required_envs


def get_aggregated_input_vars(clickCtx, role_config_dir_path, role_name, params, additional_input_vars):
    default_vars = utils.get_default_vars(clickCtx)
    required_envs = []
    aggregated_input_vars = {}

    role_group_name = role_name.split("-")[0]
    for key in default_vars.get(role_group_name, {}):
        aggregated_input_vars[str.upper(key)] = default_vars[role_group_name][key]

    # Load config.yaml in the role. Read input_env and overwrite the environment value if there is default field
    with open(role_config_dir_path + "/config.yaml", "r") as file:
        role_config_vars = yaml.safe_load(file)
        for input_env in role_config_vars["role"]["input_env"]:
            for default_env in input_env:
                if "required" in default_env:
                    required_envs.append(input_env["name"])
                if "default" in default_env:
                    aggregated_input_vars[input_env["name"]] = input_env["default"]

    # If it is unit, add additional input variables
    if additional_input_vars is not None:
        for input_var, value in additional_input_vars.items():
            aggregated_input_vars[input_var] = value

    # If user put params, it will overwrite environment variable
    ignore_validate_input_env = context["config"]["ignore_validate_input_env"]
    # ignore_validate_input_env = clickCtx.obj.get("config", "config_data")["config_data"]["ignore_validate_input_env"]
    if params is not None:
        for param in params:
            if ignore_validate_input_env:
                aggregated_input_vars[param] = params[param]
            else:
                for input_env in role_config_vars["role"]["input_env"]:
                    if input_env["name"].lower() == param.lower():
                        aggregated_input_vars[input_env["name"]] = params[param]

    # print(f"{Fore.GREEN} \u21B3 Successfully aggregated input variables {Fore.RESET}")
    logger.info(f"{Fore.GREEN} \u21b3 Successfully aggregated input variables {Fore.RESET}")
    # print(f"{Fore.GREEN} \u21B3 {aggregated_input_vars} {Fore.RESET}")
    # logger.debug(f"JHOUSE{Fore.GREEN} \u21B3 {aggregated_input_vars} {Fore.RESET}")
    return aggregated_input_vars, required_envs


def verify_required_env_exist(required_envs):
    for required_env in required_envs:
        if required_env not in os.environ:
            # print(f"{Fore.RED}Required environment value({required_env}) is not set{Fore.RESET}")
            logger.error(f"{Fore.RED}Required environment value({required_env}) is not set{Fore.RESET}")
            exit(1)
    # print(f"{Fore.GREEN} \u21B3 successfully confirmed that all required input variables have been entered{Fore.RESET}")
    logger.info(f"{Fore.GREEN} \u21b3 successfully confirmed that all required input variables have been entered{Fore.RESET}")


def validate_output_env_file(output_env_file_path, role_config_dir_path):
    with open(role_config_dir_path + "/config.yaml", "r") as file:
        target_component_vars = yaml.safe_load(file)
        utils.set_env_vars_if_file_exist(output_env_file_path)
        if "output_env" in target_component_vars["role"]:
            for output_env in target_component_vars["role"]["output_env"]:
                if str(output_env["name"]) not in os.environ:
                    logger.error(f"{Fore.RED}Please checkt this role. output_env({output_env}) is not set{Fore.RESET}")
                    exit(1)
            # print(f"{Fore.GREEN} \u21B3 All required environment variables are successfully set for the next role{Fore.RESET}")
            logger.info(f"{Fore.GREEN} \u21b3 All required environment variables are successfully set for the next role{Fore.RESET}")
        else:
            # print(f"{Fore.GREEN} \u21B3 No output variables are required for this role{Fore.RESET}")
            logger.info(f"{Fore.GREEN} \u21b3 No output variables are required for this role{Fore.RESET}")
            return


def get_role_config_dir_path(role_list, role_name):
    target_config_yaml_dir_path = None
    for item in role_list:
        if role_name == item["name"]:
            target_config_yaml_dir_path = item["path"]
    if target_config_yaml_dir_path is None:
        # print(f"{Fore.RED}role({role_name} does not exist){Fore.RESET}")
        logger.error(f"{Fore.RED}role({role_name} does not exist){Fore.RESET}")
        exit(1)
    return target_config_yaml_dir_path


def get_output_env_file_path(index, output_dir, role_config_dir_path, param_output_env_file):
    target_output_file_path = ""
    with open(role_config_dir_path + "/config.yaml", "r") as file:
        target_component_vars = yaml.safe_load(file)
        if "output_env" in target_component_vars["role"]:
            if "output_filename" in target_component_vars["role"]:
                if index is not None:
                    target_output_file_path = os.path.join(output_dir, f"{index}-{target_component_vars['role']['output_filename']}")
                else:
                    target_output_file_path = os.path.join(output_dir, target_component_vars["role"]["output_filename"])

        if param_output_env_file is not None:
            target_output_file_path = param_output_env_file
        else:
            if index is not None:
                target_output_file_path = os.path.join(output_dir, f"{index}-{target_component_vars['role']['name']}-output.sh")
            else:
                target_output_file_path = os.path.join(output_dir, target_component_vars["role"]["name"] + "-output.sh")
    return target_output_file_path


