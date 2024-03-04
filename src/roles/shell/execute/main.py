#!/usr/bin/env python
import os
import subprocess
import yaml

## INIT START ##   
def find_root_directory(cur_dir):
    while not os.path.isdir(os.path.join(cur_dir, '.git')) and cur_dir != '/':
        cur_dir = os.path.dirname(cur_dir)
    if os.path.isdir(os.path.join(cur_dir, '.git')):
        return cur_dir
    else:
        return None

current_dir = os.path.dirname(os.path.abspath(__file__))
root_directory = find_root_directory(current_dir)
if root_directory:
    print(f"The root directory is: {root_directory}")
else:
    print("Error: Unable to find .git folder.")

config_yaml_file=os.path.join(current_dir,"config.yaml")
with open(config_yaml_file, "r") as config_file:
    config_data = yaml.safe_load(config_file)

with open(f"{root_directory}/config.txt", 'r') as file:
    config_dict_str = file.read()
    config_dict = eval(config_dict_str)

OUTPUT_DIR=config_dict['output_dir']
ARTIFACTS_DIR=config_dict['artifacts_dir']
if os.environ['ROLE_DIR'] =="":
    ROLE_DIR=config_dict['role_dir']
else:
    ROLE_DIR=os.environ['ROLE_DIR']
if os.environ['REPORT_FILE'] == "":    
    REPORT_FILE=config_dict['report_file']    
else:
    REPORT_FILE=os.environ['REPORT_FILE']
## INIT END ##
#################################################################
index_role_name=os.path.basename(ROLE_DIR)
role_name = config_data.get("role", {}).get("name", "")

commands_list = os.environ.get("COMMANDS", "").split("%%")

for index, command in enumerate(commands_list):
    command = command.strip()
    if command:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)         
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

            ############# REPORT #############                           
            with open(f"{REPORT_FILE}", "a") as report_file:
                report_file.write(f"{index_role_name}::command::{index}::{result.returncode}\n")
        except Exception as e:
            print(f"Error occurred while executing command '{command}': {e}")
