import os
import re
import argparse
import sys

# Argument parser
parser = argparse.ArgumentParser(description='Update main.sh files with common.sh content.')
parser.add_argument('file_extension', nargs='?', choices=['py', 'sh'], default='sh', help='Specify the file extension (py or sh).')

args = parser.parse_args()

def find_root_directory(cur_dir):
    while not os.path.isdir(os.path.join(cur_dir, ".git")) and cur_dir != "/":
        cur_dir = os.path.dirname(cur_dir)
    if os.path.isdir(os.path.join(cur_dir, ".git")):
        return cur_dir
    else:
        return None

current_dir = os.path.dirname(os.path.abspath(__file__))
root_directory = find_root_directory(current_dir)

# read commons.sh/commons.py
target_common_file_path = f'{current_dir}/commons.{args.file_extension}'
with open(target_common_file_path, "r") as common_file:
    common_content = common_file.read()

# Remove blank lines from commons contents
common_content = "\n".join([line for line in common_content.split("\n") if line.strip() != ""])

# Set role directory
target_directory = f"{root_directory}/src/roles"

def update_script(file_path):
    with open(file_path, "r") as script_file:
        script_content = script_file.read()

    # Find ## INIT START ## / ## INIT END ##
    start_placeholder = "## INIT START ##"
    end_placeholder = "## INIT END ##"

    # Remove from start to end
    pattern = re.compile(rf"{start_placeholder}.*?{end_placeholder}", re.DOTALL)

    if pattern.search(script_content):
        # add commons contents
        new_content = f"{start_placeholder}\n{common_content}\n{end_placeholder}"
        updated_content = re.sub(pattern, new_content, script_content)

        # update file
        with open(file_path, "w") as script_file:
            script_file.write(updated_content)
        print(f"Updated {file_path}")
    else:
        print(f"Placeholders not found in {file_path}")


# From the role directory, find main.sh or main.py
for root, dirs, files in os.walk(target_directory):
    for file in files:
        if file == f'main.{args.file_extension}':
            file_path = os.path.join(root, file)
            update_script(file_path)

print("All scripts updated.")
