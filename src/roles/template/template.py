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
# Load python utils
src_dir = os.path.join(root_directory, "src")
sys.path.append(src_dir)
import commons.python.py_utils as py_utils
from core.report_manager import LoopyReportManager

ROLE_DIR = os.environ["ROLE_DIR"]
REPORT_FILE = os.environ["REPORT_FILE"]
LOOPY_RESULT_DIR = os.environ["LOOPY_RESULT_DIR"]

reportManager = LoopyReportManager(LOOPY_RESULT_DIR)
reportManager.load_role_time()
## INIT END ##

#################################################################
import time

results = []
index_role_name = os.path.basename(ROLE_DIR)
role_name = config_data.get("role", {}).get("name", "")

############# Update role time ##############
start_time = reportManager.role_time_dict["start_time"]
end_time = reportManager.role_time_dict["end_time"]
    
start_time.append(time.time())
end_time.append(time.time())
reportManager.update_role_time("start_time", start_time)
reportManager.update_role_time("end_time", end_time)

############# Update command output ##############
with open(f"{ROLE_DIR}/artifacts.txt", "w") as each_command_output_file:
    temp_result = 0
    each_command_output_file.write(f"######## YOUR ROLE #######\n")    


############# VERIFY #############


############# OUTPUT #############
with open(os.environ["OUTPUT_ENV_FILE"], "a") as output_file:
    output_file.write(f"MINIO_S3_SVC_URL=http://minio.{os.environ['MINIO_NAMESPACE']}.svc.cluster.local:9000\n")


############# REPORT #############
with open(f"{REPORT_FILE}", "a") as report_file:
    for result in results:
        report_file.write(f"{result}\n")
