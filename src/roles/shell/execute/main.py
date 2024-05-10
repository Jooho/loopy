#!/usr/bin/env python
import os
import subprocess
import yaml
import sys
import time


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
    print(f"The root directory is: {root_directory}")
else:
    print("Error: Unable to find .git folder.")

config_yaml_file = os.path.join(current_dir, "config.yaml")
with open(config_yaml_file, "r") as config_file:
    config_data = yaml.safe_load(config_file)

with open(f"config.txt", "r") as file:
    config_dict_str = file.read()
    config_dict = eval(config_dict_str)

# Load python utils
script_dir = os.path.join(root_directory, "commons", "python")
sys.path.append(root_directory)
sys.path.append(script_dir)
import py_utils
from config import summary_dict,update_summary,load_summary

OUTPUT_DIR = config_dict["output_dir"]
ARTIFACTS_DIR = config_dict["artifacts_dir"]
if os.environ["ROLE_DIR"] == "":
    ROLE_DIR = config_dict["role_dir"]
else:
    ROLE_DIR = os.environ["ROLE_DIR"]
if os.environ["REPORT_FILE"] == "":
    REPORT_FILE = config_dict["report_file"]
else:
    REPORT_FILE = os.environ["REPORT_FILE"]
## INIT END ##

#################################################################
index_role_name = os.path.basename(ROLE_DIR)
role_name = config_data.get("role", {}).get("name", "")

commands_list = os.environ.get("COMMANDS", "").split("%%")
results = []
errorHappened = 1  # 0 is true, 1 is false

load_summary()
start_time=summary_dict["start_time"]
if "end_time" in summary_dict:
    end_time=summary_dict["end_time"]
else:
    end_time=[]    
for index, command in enumerate(commands_list):
    load_summary()
    command = command.strip()
    if command.strip() != '':
        try:
            if not command.startswith("#"):
                start_time.append(time.time())
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                end_time.append(time.time())
                update_summary("start_time", start_time)
                update_summary("end_time", end_time)

                print(result.stdout, end="")  # print to stdout to pass it to log file
                with open(f"{ROLE_DIR}/{index}-command.txt", "w") as each_command_output_file:
                    each_command_output_file.write(f"######## {index} command #######\n")
                    each_command_output_file.write(f"COMMAND: {command}\n")
                    each_command_output_file.write("STDOUT: ")
                    each_command_output_file.write(result.stdout)
                    each_command_output_file.write("\n\n")
                    if result.stderr:
                        each_command_output_file.write("STDERR:\n")
                        each_command_output_file.write(result.stderr)
                        each_command_output_file.write("\n")
                        errorHappened = "0"

                with open(f"{ROLE_DIR}/commands.txt", "a") as all_command_output_file:
                    all_command_output_file.write(f"######## {index} command #######\n")
                    all_command_output_file.write(f"COMMAND: {command}\n")
                    all_command_output_file.write("STDOUT: ")
                    all_command_output_file.write(result.stdout)
                    all_command_output_file.write("\n\n")
                    if result.stderr:
                        all_command_output_file.write("STDERR:\n")
                        all_command_output_file.write(result.stderr)
                        all_command_output_file.write("\n")
                        errorHappened = "0"
                    results.append(f"{index_role_name}::command::{index+1}::{result.returncode}")


        except Exception as e:
            print(f"Error occurred while executing command '{command}': {e}")
    
    if errorHappened == "0":
        print("There are some errors in the role")
        stop_when_failed = py_utils.is_positive(os.environ["STOP_WHEN_FAILED"])
        if stop_when_failed == "0":
            print(f"STOP_WHEN_FAILED({os.environ['STOP_WHEN_FAILED']}) is set and there are some errors detected so stop all process")
            sys.exit(10)
        else:
            print(f"STOP_WHEN_FAILED({os.environ['STOP_WHEN_FAILED']}) is NOT set so skip this error.")

    ############# REPORT #############

with open(f"{REPORT_FILE}", "a") as report_file:
    if len(results) > 1:
        if errorHappened == "0":
            report_file.write(f"{index_role_name}::command::0::1\n")
        else:
            report_file.write(f"{index_role_name}::command::0::0\n")
    for result in results:
        report_file.write(f"{result}\n")
