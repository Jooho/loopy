# core/initializer.py

import os
from datetime import datetime

from core.env import EnvManager
from config import update_config, reset_config, reset_summary


class Initializer:
    def __init__(self, default_vars: dict):
        self.vars = default_vars
        self.now = datetime.now()
        self.root_dir = self.vars["cli"]["output_root_dir"]
        self.date_dir = os.path.join(self.root_dir, self.now.strftime("%Y%m%d_%H%M"))

    def initialize_roles(self):
        # 역할 디렉토리 경로를 config_loader에서 가져옵니다.
        roles_dir_list = self.config_loader.get_roles_dirs()
        
        # 역할 초기화
        role_list = []
        for directory in roles_dir_list:
            roles = utils.initialize(directory, "role")
            role_list.extend(roles)
        
        return role_list
    
    def initialize(self):
        reset_config()
        reset_summary()

        output_dir = os.path.join(self.date_dir, self.vars["cli"]["output_env_dir"])
        artifacts_dir = os.path.join(self.date_dir, self.vars["cli"]["output_artifacts_dir"])
        report_file = os.path.join(self.date_dir, self.vars["cli"]["output_report_file"])

        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(artifacts_dir, exist_ok=True)

        with open(report_file, "w") as file:
            file.write("# This is a report.\n")

        update_config("output_dir", output_dir)
        os.environ["OUTPUT_DIR"] = output_dir

        update_config("artifacts_dir", artifacts_dir)
        os.environ["ARTIFACTS_DIR"] = artifacts_dir

        update_config("report_file", report_file)
        os.environ["REPORT_FILE"] = report_file

        show_debug_log = self.vars["cli"]["show_debug_log"]
        stop_when_failed = self.vars["cli"]["stop_when_failed"]
        stop_when_error_happened = self.vars["cli"]["stop_when_error_happened"]

        update_config("show_debug_log", show_debug_log)
        os.environ["SHOW_DEBUG_LOG"] = show_debug_log
        update_config("stop_when_failed", stop_when_failed)
        update_config("stop_when_error_happened", stop_when_error_happened)

        # PATH에 ./bin 추가
        bin_path = os.path.join(os.getcwd(), "bin")
        os.environ["PATH"] = f"{bin_path}:{os.environ['PATH']}"

        # Default 값 설정
        os.environ["STOP_WHEN_FAILED"] = "1"
