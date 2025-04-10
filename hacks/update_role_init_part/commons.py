import os
import yaml
import sys

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
from core.config import summary_dict,update_summary,load_summary

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
