# core/initializer.py

import os
import re
import yaml
import shutil
from datetime import datetime
from jsonschema import Draft7Validator

import logging
from core.report_manager import LoopyReportManager
from core.context import LoopyContextBuilder
from colorama import Fore, Style


class Initializer:

    def __init__(self, env_list, config_data, default_vars: dict):
        self.logger = logging.getLogger(__name__)
        self.env_list = env_list
        self.config_data = config_data
        self.default_vars = default_vars

        # Overwrite the config with environment variables if they exist, as they take higher priority
        self.sync_env_to_config(self.env_list, self.config_data)
        self.now = datetime.now()
        self.loopy_root_path = self.config_data["loopy_root_path"]
        self.output_root_dir = self.config_data["output_root_dir"]
        # result folder format
        target_report_dir = self.now.strftime("%Y%m%d_%H%M")
        if self.config_data.get("output_target_dir"):
            target_report_dir = self.config_data["output_target_dir"]
        self.loopy_result_dir = os.path.join(self.output_root_dir, target_report_dir)

        # if self.config_data.get("loopy_result_dir"):
        #     self.loopy_result_dir = self.config_data["loopy_result_dir"]
        self.config_data["loopy_result_dir"] = self.loopy_result_dir

    def initialize(self):
        # Initialize result directory
        output_dir = os.path.join(self.loopy_result_dir, self.config_data["output_env_dir"])
        artifacts_dir = os.path.join(self.loopy_result_dir, self.config_data["output_artifacts_dir"])
        report_file = os.path.join(self.loopy_result_dir, self.config_data["output_report_file"])

        # Update config data with paths
        self.config_data["output_dir"] = output_dir
        self.config_data["artifacts_dir"] = artifacts_dir
        self.config_data["report_file"] = report_file

        # Set environment variables
        os.environ["OUTPUT_DIR"] = output_dir
        os.environ["ARTIFACTS_DIR"] = artifacts_dir
        os.environ["REPORT_FILE"] = report_file

        # Create output/artifacts directories

        if output_dir and os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        if artifacts_dir and os.path.exists(artifacts_dir):
            shutil.rmtree(artifacts_dir)
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(artifacts_dir, exist_ok=True)

        # Reset temporary data for each run
        reportManager = LoopyReportManager(self.loopy_result_dir)
        reportManager.init_report_data()
        reportManager.reset_role_time()
        reportManager.reset_summary()

        # Create report file
        with open(report_file, "w") as file:
            file.write("# This is a report.\n")

        # Set logging and error handling configurations
        show_debug_log = self.config_data["show_debug_log"]
        stop_when_failed = self.config_data["stop_when_failed"]
        stop_when_error_happened = self.config_data["stop_when_error_happened"]

        # Update config data with paths
        self.config_data["show_debug_log"] = show_debug_log
        self.config_data["stop_when_failed"] = stop_when_failed
        self.config_data["stop_when_error_happened"] = stop_when_error_happened

        # Set environment variables
        os.environ["SHOW_DEBUG_LOG"] = show_debug_log
        os.environ["STOP_WHEN_FAILED"] = stop_when_error_happened
        os.environ["STOP_WHEN_ERROR_HAPPENED"] = stop_when_error_happened

        # Set binary path
        bin_path = os.path.join(os.getcwd(), "bin")
        os.environ["PATH"] = f"{bin_path}:{os.environ['PATH']}"

        # Add Schema paths
        self.config_data["schema"] = {
            "role": f"{self.loopy_root_path}/src/schema/role.yaml",
            "unit": f"{self.loopy_root_path}/src/schema/unit.yaml",
            "playbook": f"{self.loopy_root_path}/src/schema/playbook.yaml",
        }

        # Add default components paths
        self.config_data["default_roles_dir"] = f"{self.loopy_root_path}/default_provided_services/roles"
        self.config_data["default_units_dir"] = f"{self.loopy_root_path}/default_provided_services/units"
        self.config_data["default_playbooks_dir"] = f"{self.loopy_root_path}/default_provided_services/playbooks"

        # Initialize the list of components
        self.initialize_component_list("role")
        self.initialize_component_list("unit")
        self.initialize_component_list("playbook")

        # Initialize the context
        return {"default_vars": self.default_vars, "config": self.config_data, "env": self.env_list}


    def sync_env_to_config(self, env: dict, config: dict):
        for key, value in env.items():
            config[key] = value

    def initialize_component_list(self, list_type):
        if list_type == "role":
            default_dir = self.config_data["default_roles_dir"]
            additional_dirs = self.config_data["additional_role_dirs"]
            key = "role_list"
        elif list_type == "unit":
            default_dir = self.config_data["default_units_dir"]
            additional_dirs = self.config_data["additional_unit_dirs"]
            key = "unit_list"
        elif list_type == "playbook":
            default_dir = self.config_data["default_playbooks_dir"]
            additional_dirs = self.config_data["additional_playbook_dirs"]
            key = "playbook_list"
        else:
            raise ValueError("Invalid list type")

        # Combine default and additional directories
        dirs_list = [default_dir] + additional_dirs

        # initialize the list
        item_list = []
        for directory in dirs_list:
            items = self.get_component_list_from_directory(directory, list_type)
            item_list.extend(items)

        # add the list to config_data
        self.config_data[key] = item_list

    def get_component_list_from_directory(self, directory, type):
        item_list = []

        for root, dirs, files in os.walk(directory):
            if "config.yaml" in files:
                config_path = os.path.join(root, "config.yaml")

                file_errors = self.validate_config_yaml_schema(config_path, type)
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
                                name = self.convert_path_to_component_name(path, type)
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
                                name = self.convert_path_to_component_name(path, type)
                            item_list.append({"name": name, "path": path})
        return item_list

    def convert_path_to_component_name(self, path, component):
        pattern = r"/" + component + "s/(.*)/(.*)$"
        match = re.search(pattern, path + "/")
        if match:
            dir_names = match.group(1).split("/")
            component_name = "-".join(dir_names)
            return f"{component_name}"
        else:
            return None

    def validate_config_yaml_schema(self, yaml_file, type):
        schema = None
        schema_file_path = None
        # Load schema file
        if type == "role":
            schema_file_path = self.config_data["schema"].get("role")
        elif type == "unit":
            schema_file_path = self.config_data["schema"].get("unit")
        elif type == "playbook":
            schema_file_path = self.config_data["schema"].get("playbook")

        with open(schema_file_path, "r") as schema_file:
            schema = yaml.safe_load(schema_file)

        # Load Target yaml file
        try:
            with open(yaml_file, "r") as f:
                yaml_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            # print(f"{Fore.RED}YAML File Syntax Error:{Style.RESET_ALL}", e)
            self.logger.error(f"YAML File Syntax Error: {e}")
            exit(1)

        # Create validator
        validator = Draft7Validator(schema)

        # Validate YAML Data
        errors = []
        for error in validator.iter_errors(yaml_data):
            errors.append({"message": error.message, "path": list(error.path)})
        return errors
