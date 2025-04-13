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
# Load python utils
script_dir = os.path.join(root_directory, "commons", "python")
src_dir = os.path.join(root_directory, "src")
sys.path.append(src_dir)
sys.path.append(script_dir)
import py_utils

from core.report_manager import LoopyReportManager

ROLE_DIR = os.environ["ROLE_DIR"]
REPORT_FILE = os.environ["REPORT_FILE"]
LOOPY_RESULT_DIR = os.environ["LOOPY_RESULT_DIR"]

reportManager = LoopyReportManager(LOOPY_RESULT_DIR)
reportManager.load_role_time()