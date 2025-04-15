#!/usr/bin/env python
import os
import sys
import subprocess
import yaml


## INIT START ##
def find_root_directory(cur_dir):
    while not os.path.isdir(os.path.join(cur_dir, ".git")) and cur_dir != "/":
        cur_dir = os.path.dirname(cur_dir)
    if os.path.isdir(os.path.join(cur_dir, ".git")):
        return cur_dir
    else:
        return None


current_dir = os.path.dirname(os.path.abspath(__file__))
root_directory = find_root_directory(current_dir)
if root_directory:
    if os.getenv("DEBUG") == "1" or os.getenv("DEBUG", "").lower() == "true":
        print(f"The root directory is: {root_directory}")
else:
    print("Error: Unable to find .git folder.")
config_yaml_file = os.path.join(current_dir, "config.yaml")
with open(config_yaml_file, "r") as config_file:
    config_data = yaml.safe_load(config_file)
# Load python utils
script_dir = os.path.join(root_directory, "commons", "python")
src_dir = os.path.join(root_directory, "src")
sys.path.append(src_dir)
sys.path.append(script_dir)
import py_utils

from core.report_manager import LoopyReportManager

# Check for required environment variables
required_vars = ["ROLE_DIR", "REPORT_FILE", "LOOPY_RESULT_DIR"]
missing_vars = [var for var in required_vars if var not in os.environ]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

ROLE_DIR = os.environ["ROLE_DIR"]
REPORT_FILE = os.environ["REPORT_FILE"]
LOOPY_RESULT_DIR = os.environ["LOOPY_RESULT_DIR"]

reportManager = LoopyReportManager(LOOPY_RESULT_DIR)
reportManager.load_role_time()
## INIT END ##

#################################################################
index_role_name = os.path.basename(ROLE_DIR)
role_name = config_data.get("role", {}).get("name", "")

if os.environ["ROLE_DIR"]:
    ROLE_DIR = os.environ["ROLE_DIR"]
commands_list = os.environ.get("COMMANDS", "").split("%%")

for index, command in enumerate(commands_list):
    command = command.strip()
    if command:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            with open(f"{ROLE_DIR}/{index}-command.txt", "w") as log_file:
                log_file.write(f"######## {index} command #######\n")
                log_file.write(f"COMMAND: {command}\n")
                log_file.write("STDOUT: ")
                log_file.write(result.stdout)
                log_file.write("\n\n")
                if result.stderr:
                    log_file.write("STDERR:\n")
                    log_file.write(result.stderr)
                    log_file.write("\n")

            with open(f"{ROLE_DIR}/commands.txt", "a") as log_file:
                log_file.write(f"######## {index} command #######\n")
                log_file.write(f"COMMAND: {command}\n")
                log_file.write("STDOUT: ")
                log_file.write(result.stdout)
                log_file.write("\n\n")
                if result.stderr:
                    log_file.write("STDERR:\n")
                    log_file.write(result.stderr)
                    log_file.write("\n")

            ############# REPORT #############
            with open(f"{REPORT_FILE}", "a") as log_file:
                log_file.write(f"{index_role_name}::command::{index}::{result.returncode}\n")
        except Exception as e:
            print(f"Error occurred while executing command '{command}': {e}")
