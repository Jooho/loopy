#!/usr/bin/env python
## INIT START ##
import os
import sys

import yaml

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
    if os.getenv("DEBUG") == "0":
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

from config import load_summary, summary_dict, update_summary

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
import subprocess
import time

index_role_name = os.path.basename(ROLE_DIR)
role_name = config_data.get("role", {}).get("name", "")

commands_list = os.environ.get("COMMANDS", "").split("%%")
results = []

load_summary()
start_time = summary_dict["start_time"]
if "end_time" in summary_dict:
    end_time = summary_dict["end_time"]
else:
    end_time = []
for index, command in enumerate(commands_list):
    load_summary()
    command = command.strip()
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    rcresult = {"stdout": "", "stderr": "", "returncode": None}
    if command.strip() != "":
        try:
            if not command.startswith("#"):
                start_time.append(time.time())
                
                showCommand=py_utils.is_positive(os.environ["SHOW_COMMAND"])
                if showCommand == 0:
                    print(command, end="\n")  
 
                with subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    close_fds=True,
                ) as process:
                    try:
                        for line in process.stdout:
                            print(line, end="")  # Print in real time
                            rcresult["stdout"] += line  # store stdout to result
                        for line in process.stderr:
                            print(line, end="", file=sys.stderr) # Print in real time
                            rcresult["stderr"] += line  # store stderr to result
                    except Exception as e:
                        print(f"Error occurred: {e}")
                process.wait()
                rcresult["returncode"] = process.returncode
                
                end_time.append(time.time())
                update_summary("start_time", start_time)
                update_summary("end_time", end_time)
                
                with open(f"{ROLE_DIR}/{index}-command.txt", "w") as each_command_output_file:
                    temp_result=0
                    each_command_output_file.write(f"######## {index} command #######\n")
                    each_command_output_file.write(f"COMMAND: {command}\n")
                    each_command_output_file.write("STDOUT: ")
                    if isinstance(rcresult["stdout"], str):
                        each_command_output_file.write(rcresult["stdout"])
                    each_command_output_file.write("\n\n")
                    if rcresult["stderr"]:
                        each_command_output_file.write("STDERR:\n")
                        if isinstance(rcresult["stderr"], str):
                            each_command_output_file.write(rcresult["stderr"])
                        # each_command_output_file.write(result.stderr)
                        each_command_output_file.write("\n")
                        temp_result=1
                        py_utils.stop_when_error_happended(temp_result, index_role_name, REPORT_FILE)

                with open(f"{ROLE_DIR}/commands.txt", "a") as all_command_output_file:
                    temp_result=0
                    all_command_output_file.write(f"######## {index} command #######\n")
                    all_command_output_file.write(f"COMMAND: {command}\n")
                    all_command_output_file.write("STDOUT: ")                   
                    if isinstance(rcresult["stdout"], str):
                        all_command_output_file.write(rcresult["stdout"])
                    all_command_output_file.write("\n\n")
                    if rcresult["stderr"]:
                        all_command_output_file.write("STDERR:\n")
                        if isinstance(rcresult["stderr"], str):
                            all_command_output_file.write(rcresult["stderr"])
                        all_command_output_file.write("\n")
                        temp_result=1
                        py_utils.stop_when_error_happended(temp_result, index_role_name, REPORT_FILE)
                    results.append(f"{index_role_name}::command::{index+1}::{temp_result}")

        except Exception as e:
            print(f"Error occurred while executing command '{command}': {e}")

############# REPORT #############
with open(f"{REPORT_FILE}", "a") as report_file:
    for result in results:
        report_file.write(f"{result}\n")
