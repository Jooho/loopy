# core/initializer.py

import os
from datetime import datetime

from core.env import EnvManager
from config import update_config, reset_config, reset_summary
from core.context import set_context, get_context
from core.context import LoopyContextBuilder
# from cli import utils


class Initializer:

    def __init__(self, env_list, config_data, default_vars: dict):
        self.env_list = env_list
        self.config_data = config_data
        self.default_vars = default_vars
        sync_env_to_config(self.env_list, self.config_data)
        self.now = datetime.now()
        self.output_root_dir = self.default_vars["cli"]["output_root_dir"]
        self.date_dir = os.path.join(
            self.output_root_dir, self.now.strftime("%Y%m%d_%H%M"))

    def initialize(self):
        reset_config()
        reset_summary()

        ctx = get_context()
        output_dir = os.path.join(
            self.date_dir, self.default_vars["cli"]["output_env_dir"])
        artifacts_dir = os.path.join(
            self.date_dir, self.default_vars["cli"]["output_artifacts_dir"])
        report_file = os.path.join(
            self.date_dir, self.default_vars["cli"]["output_report_file"])

        # Create output/artifacts directories
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(artifacts_dir, exist_ok=True)

        # Create report file
        with open(report_file, "w") as file:
            file.write("# This is a report.\n")

        self.update_config_data("output_dir", output_dir)
        os.environ["OUTPUT_DIR"] = output_dir

        # update_config("output_dir", output_dir)

        self.update_config_data("artifacts_dir", artifacts_dir)
        # update_config("artifacts_dir", artifacts_dir)
        os.environ["ARTIFACTS_DIR"] = artifacts_dir

        self.update_config_data("report_file", report_file)
        # update_config("report_file", report_file)
        os.environ["REPORT_FILE"] = report_file

        show_debug_log = self.default_vars["cli"]["show_debug_log"]
        stop_when_failed = self.default_vars["cli"]["stop_when_failed"]
        stop_when_error_happened = self.default_vars["cli"]["stop_when_error_happened"]

        self.update_config_data("show_debug_log", show_debug_log)
        # update_config("show_debug_log", show_debug_log)
        os.environ["SHOW_DEBUG_LOG"] = show_debug_log

        self.update_config_data("stop_when_failed", stop_when_failed)
        os.environ["STOP_WHEN_FAILED"] = stop_when_error_happened
        self.update_config_data("stop_when_error_happened",
                                stop_when_error_happened)
        os.environ["STOP_WHEN_ERROR_HAPPENED"] = stop_when_error_happened

        bin_path = os.path.join(os.getcwd(), "bin")
        os.environ["PATH"] = f"{bin_path}:{os.environ['PATH']}"

        # Default 값 설정
        self.config_data["schema"] = {
            "role": f"{self.env_list['loopy_root_path']}/src/schema/role.yaml",
            "unit": f"{self.env_list['loopy_root_path']}/src/schema/unit.yaml",
            "playbook": f"{self.env_list['loopy_root_path']}/src/schema/playbook.yaml",
        }
        LoopyContextBuilder(self.env_list, self.default_vars,
                            self.config_data).build()

    def update_config_data(self, key: str, value):
        self.config_data[key] = value


def sync_env_to_config(env: dict, config: dict):
    for key, value in env.items():
        config[key] = value


def initialize_roles(self):
    # Get config_loader for roles dir list
    roles_dir_list = self.config_loader.get_roles_dirs()

    # 역할 초기화
    role_list = []
    for directory in roles_dir_list:
        roles = utils.initialize(directory, "role")
        role_list.extend(roles)

    return role_list
