from collections import defaultdict
import os
from cli.commands import utils

from colorama import Fore, Style
from core.config import summary_dict, load_summary
from prettytable import PrettyTable
from cli.commands import constants

def summary(ctx, type, config_data, unit_list):
    load_summary()
    print(f'{Fore.RESET}')  # Reset Color
    summary_text = ["╦  ╔═╗╔═╗╔═╗╦ ╦", "║  ║ ║║ ║╠═╝╚╦╝", "╩═╝╚═╝╚═╝╩   ╩ ",
                    "╔═╗┬ ┬┌┬┐┌┬┐┌─┐┬─┐┬ ┬", "╚═╗│ │││││││├─┤├┬┘└┬┘", "╚═╝└─┘┴ ┴┴ ┴┴ ┴┴└─ ┴ "]
    first_component_type = summary_dict["first_component_type"]
    first_component_name = summary_dict["first_component_name"]
    loopy_result_dir = summary_dict["loopy_result_dir"]
    start_time = summary_dict["start_time"]
    end_time = summary_dict["end_time"]

    execution_time = end_time[-1] - start_time[0]
    total_minutes = int(execution_time // 60)
    total_seconds = round(float(execution_time % 60),
                          constants.REPORT_EXECUTION_TIME_ROUND)

    additional_info = [
        f"Run: {first_component_type}({first_component_name})",
        f"Loopy result dir: {loopy_result_dir}",
        f"Report file: {loopy_result_dir}/report",
        f"Execution time: {total_minutes}{constants.REPORT_MIN_UNIT} {total_seconds}{constants.REPORT_SECOND_UNIT}",
    ]

    # Find the maximum length of text lines
    max_line_length = max(len(line) for line in summary_text) + 100

    # Print top border
    print("*" * (max_line_length + 4))

    # Print text with *
    for line in summary_text:
        padding_length = (max_line_length - len(line)) // 2
        print("* " + " " * padding_length + line + " " *
              (max_line_length - len(line) - padding_length) + " *")
    # Print additional info
    for info in additional_info:
        padding_length = (max_line_length - len(info)) // 2
        key = info.split(":")[0].strip()
        value = info.split(":")[1].strip()
        new_string = f"{Fore.BLUE}{key}{Style.RESET_ALL}" + \
            ":" + f"{Fore.YELLOW} {value}{Style.RESET_ALL}"

        print("* " + " " * padding_length + new_string + " " *
              (max_line_length - len(info) - padding_length) + " *")

    # Print bottom border
    print("*" * (max_line_length + 4))

    # Report Table
    report_file = os.path.join(summary_dict["loopy_result_dir"], "report")

    # Execution time per role
    execution_time_min_list = [int((end - start) // 60)
                               for start, end in zip(start_time, end_time)]
    execution_time_sec_list = [round(float(
        (end - start)), constants.REPORT_EXECUTION_TIME_ROUND) for start, end in zip(start_time, end_time)]

    for i in range(len(execution_time_sec_list)):
        if execution_time_sec_list[i] >= 60:
            # get minutes from seconds and add to minutes list
            execution_time_min_list[i] += execution_time_sec_list[i] // 60
            # get the remaining seconds after converting to minutes
            execution_time_sec_list[i] = execution_time_sec_list[i] % 60
    
    # When it is shell-execute role, it can have multiple times,
    # Then it needs to accumulate the times to show full execution time
    execution_time_min_list, execution_time_sec_list = accumulate_time_per_role(
        report_file, execution_time_min_list, execution_time_sec_list)

    table = PrettyTable(["Index", "Role Name", "Result", "Time", "Folder"])
    if type == "playbook":
        table = get_report_table_for_playbook(
            ctx, table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data, unit_list)
    else:
        table = get_report_table_for_unit_role(
            table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data)
    print(table)


def getDescription(ctx, role_name, step_index, to_check_duplicate_role_name, py_config_data, unit_list):
    description = ""
    steps = py_config_data["playbook"]["steps"]

    step = steps[step_index]
    if "unit" in step:
        unit_name = step["unit"]["name"]
        unit_config_data = utils.get_config_data_by_name(
            ctx, unit_name, "unit", unit_list)
        for role in unit_config_data["unit"]["steps"]:
            if to_check_duplicate_role_name != 0:
                to_check_duplicate_role_name -= 1
                continue
            if role["role"]["name"] == role_name and to_check_duplicate_role_name == 0:
                if "description" in role["role"]:
                    description = role["role"]["description"]
                    break
    else:
        if step["role"]["name"] == role_name:
            if to_check_duplicate_role_name != 0:
                description = role_name
            elif "description" in step["role"]:
                description = step["role"]["description"]
    return description


def accumulate_time_per_role(report_file, execution_time_min_list, execution_time_sec_list):
    """
    Processes a report file and accumulates execution times per role.

    For each role (defined by index and name), this function:
    - Collects execution times for consecutive commands with the same role.
    - When the role changes, it appends the sum and individual times to the accumulated lists.
    - Handles both minute and second values in parallel.

    Args:
        report_file (str): Path to the report file with role-command mapping.
        execution_time_min_list (list of int/float): Per-command execution times (minutes).
        execution_time_sec_list (list of int/float): Per-command execution times (seconds).

    Returns:
        tuple: Two lists — accumulated_execution_time_min_list, accumulated_execution_time_sec_list
    """
    
    
    each_command_min = []
    each_command_sec = []
    accumulated_execution_time_min_list = []
    accumulated_execution_time_sec_list = []
    prev_role_index = None 
    prev_role_name = None
    
    report_lines = parse_report_file(report_file)
    last_report_line_index = len(report_lines) - 1
    result_idx = 0

    for line in report_lines:
        
        # Parse the line to get role index and report data
        if line[0].isdigit():
            role_index, report_data = line.split("-", 1)
        else:
            role_index = 0
            report_data = line

        result_data = report_data.split("::")
        role_name= result_data[0]            

        # Check if the current role is the same as the previous one
        # is_same_role = (
        #     prev_role_index is not None and
        #     prev_role_index == role_index and
        #     prev_role_name == role_name
        # )
        
        if prev_role_index is None or is_same_role(prev_role_index, prev_role_name, role_index, role_name):
            pass  # Keep accumulating
        else:
            append_accumulated_times(accumulated_execution_time_min_list, accumulated_execution_time_sec_list, each_command_min, each_command_sec)

            each_command_min = []
            each_command_sec = []

        # Append current execution time
        each_command_min.append(execution_time_min_list[result_idx])
        each_command_sec.append(execution_time_sec_list[result_idx])

        # On last line, finalize the remaining data
        if result_idx == last_report_line_index:
            append_accumulated_times(accumulated_execution_time_min_list, accumulated_execution_time_sec_list, each_command_min, each_command_sec)

        # Update previous role        
        prev_role_name = role_name
        prev_role_index = role_index
        result_idx += 1
            
    return accumulated_execution_time_min_list, accumulated_execution_time_sec_list


def is_same_role(prev_role_index, prev_role_name, role_index, role_name):
    """
    Check if the current role is the same as the previous role.
    """
    return prev_role_index is not None and prev_role_index == role_index and prev_role_name == role_name


def append_accumulated_times(acc_min_list, acc_sec_list, cmd_min, cmd_sec):
    """
    Accumulates and records execution time:
    - Appends the total (sum) of command times to the accumulated list.
    - Then appends each individual command's execution time.
    
    Args:
        acc_min_list (list): List to store accumulated minutes.
        acc_sec_list (list): List to store accumulated seconds.
        cmd_min (list): Current list of per-command execution times in minutes.
        cmd_sec (list): Current list of per-command execution times in seconds.
    """
    acc_min_list.append(sum(cmd_min))
    acc_min_list.extend(cmd_min)

    acc_sec_list.append(sum(cmd_sec))
    acc_sec_list.extend(cmd_sec)
    
    
def parse_report_file(report_file):
    """
    Parse the report file to extract non-empty, non-comment lines.
    This ensures we only process valid execution entries.
    """
    report_lines = []
    with open(report_file, "r") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            report_lines.append(line)
    return report_lines

   

def parse_report_line(line):
    """
    Parse a single report line and extract index, role name, and result.
    """
    if line[0].isdigit():
        index, report_data = line.split("-", 1)
    else:
        index = "0"
        report_data = line

    result_data = report_data.split("::")
    role_name = result_data[0]
    result = result_data[-1]

    return index, role_name, result

def get_report_table_for_unit_role(table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data):
    """
    Parse the report file, filter valid lines, and populate the table with the role's index, name, result, execution time, and folder path.
    """
    # Parse the report file to extract valid lines
    report_lines = parse_report_file(report_file)

    prev_role_index = None
    prev_role_sub_index = 0
    prev_role_name = None
    result_index = 0
    last_report_line_index = len(report_lines) - 1

    for line in report_lines:
        # index, report_data = line.split("-", 1) if line[0].isdigit() else ("0", line)
        # result_data = report_data.split("::")
        # role_name = result_data[0]
        # result = result_data[-1]

        role_index, role_name, role_result = parse_report_line(line)
        # Generate the final index and update sub-index if needed
        if is_same_role(prev_role_index, prev_role_name, role_index, role_name):
            sub_index = prev_role_sub_index + 1
            final_index = f"{role_index}-{sub_index}"
            prev_role_sub_index = sub_index
        else:
            final_index = role_index
            prev_role_sub_index = 0

        prev_role_index = role_index
        prev_role_name = role_name

        # Get the execution time in minutes and seconds
        exec_min_time = execution_time_min_list[result_index]
        exec_sec_time = execution_time_sec_list[result_index]

        # Get the description for the unit type
        description = ""
        if type == "unit":
            folder_path = f"{role_index}-{role_name}"
            steps = config_data[type]["steps"]
            if "description" in steps[int(role_index)]["role"]:
                description = shorten_string(
                    steps[int(role_index)]["role"]["description"],
                    constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH
                )
        if type == "role":
            folder_path = f"{role_name}"

        # Add the row to the table
        table.add_row(
            [
                final_index.strip(),
                description if description != "" else role_name.strip(),
                f"{Fore.GREEN}Success{Style.RESET_ALL}" if role_result.strip() == "0" else f"{Fore.RED}Fail{Style.RESET_ALL}",
                f"{exec_min_time}{constants.REPORT_MIN_UNIT} {exec_sec_time}{constants.REPORT_SECOND_UNIT}",
                os.path.join(loopy_result_dir, "artifacts", folder_path),
            ]
        )

        result_index += 1

    return table











def get_report_table_for_playbook(ctx, table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data, unit_list):
    py_steps = config_data["playbook"]["steps"]
    py_step_unit_role_description = []
    py_step_time_position_index_list = []
    py_step_min_time_list = []
    py_step_sec_time_list = []
    target_index = 0
    for py_step in py_steps:
        temp_min_time = 0
        temp_sec_time = 0.0
        if "unit" in py_step:
            unit_name = py_step["unit"]["name"]
            if "description" in py_step["unit"]:
                py_step_unit_role_description.append(
                    py_step["unit"]["description"])
            else:
                py_step_unit_role_description.append(unit_name)
            unit_config_data = utils.get_config_data_by_name(
                ctx, unit_name, type, unit_list)
            unit_steps = unit_config_data["unit"]["steps"]
            command_count = 0
            py_step_time_position_index_list.append(target_index)
            for role in unit_steps:
                if "shell-execute" == role["role"]["name"]:
                    commands_list = role["role"]["input_env"]["COMMANDS"].split(
                        "%%")
                    for command in commands_list:
                        if command.strip() != '':
                            command_count += 1
                    temp_min_time += execution_time_min_list[target_index]
                    temp_sec_time += execution_time_sec_list[target_index]
                    target_index += command_count
                    if command_count >= 2:
                        target_index += 1
                else:
                    temp_min_time += execution_time_min_list[target_index]
                    temp_sec_time += execution_time_sec_list[target_index]
                    target_index += 1
            py_step_min_time_list.append(temp_min_time)
            py_step_sec_time_list.append(temp_sec_time)
        else:
            if "description" in py_step["role"]:
                py_step_unit_role_description.append(
                    py_step["role"]["description"])
            else:
                py_step_unit_role_description.append(py_step["role"]["name"])
            py_step_time_position_index_list.append(target_index)
            command_count = 0
            if "shell-execute" == py_step["role"]["name"]:
                commands_list = py_step["role"]["input_env"]["COMMANDS"].split(
                    "%%")
                for command in commands_list:
                    if command.strip() != '':
                        command_count += 1
                temp_min_time += execution_time_min_list[target_index]
                temp_sec_time += execution_time_sec_list[target_index]
                target_index += command_count
                if command_count >= 2:
                    target_index += 1
            else:
                temp_min_time += execution_time_min_list[target_index]
                temp_sec_time += execution_time_sec_list[target_index]
                target_index += 1
            py_step_min_time_list.append(temp_min_time)
            py_step_sec_time_list.append(temp_sec_time)

    with open(f"{report_file}", "r") as file:
        data = file.readlines()
        prev_index = "-1"
        prev_sub_index = 0
        prev_role_name = None
        final_index = None
        sub_index = 0
        exec_min_time = 0.0
        exec_sec_time = 0.0
        result_line = 0
        to_check_duplicate_role_name = 0
        for line in data:
            line = line.strip()  # Delete enter
            if not line or line.startswith("#"):  # Skip # part
                continue
            # if it has index
            if line[0].isdigit():
                index, report_data = line.split("-", 1)
            else:
                index = "0"
                report_data = line

            result_data = report_data.split("::")  # separate data by "::""
            role_name = result_data[0]
            result = result_data[-1]

            if prev_index == index and prev_role_name == role_name:
                sub_index = prev_sub_index + 1
                final_index = f"{index}-{sub_index}"
                prev_sub_index = prev_sub_index + 1
            else:
                final_index = index
                prev_index = index
                prev_role_name = role_name
                prev_sub_index = 0
                sub_index = 0

            exec_min_time = execution_time_min_list[result_line]
            exec_sec_time = execution_time_sec_list[result_line]
            description = ""
            if type == "playbook":
                if result_line in py_step_time_position_index_list:
                    accumulate_time_index_per_unit_role = py_step_time_position_index_list.index(
                        result_line)
                    to_check_duplicate_role_name = 0
                else:
                    to_check_duplicate_role_name += 1

                description = shorten_string(
                    getDescription(ctx, role_name, accumulate_time_index_per_unit_role, to_check_duplicate_role_name,
                                   config_data, unit_list), constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH
                )

            if result_line in py_step_time_position_index_list:
                accumulate_time_index_per_unit_role = py_step_time_position_index_list.index(
                    result_line)
                unit_description = shorten_string(
                    py_step_unit_role_description[accumulate_time_index_per_unit_role], constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH)
                table.add_row(
                    [
                        f"{Fore.YELLOW}Step({accumulate_time_index_per_unit_role})",
                        f"{unit_description}",
                        f"\u21A7",
                        f"{py_step_min_time_list[accumulate_time_index_per_unit_role]}{constants.REPORT_MIN_UNIT} {round(py_step_sec_time_list[accumulate_time_index_per_unit_role],constants.REPORT_EXECUTION_TIME_ROUND)}{constants.REPORT_SECOND_UNIT}{Style.RESET_ALL}",
                        "",
                    ]
                )

            table.add_row(
                [
                    f"R({final_index.strip()})",
                    description if description != "" else role_name.strip(),
                    f"{Fore.GREEN}Success{Style.RESET_ALL}" if result.strip(
                    ) == "0" else f"{Fore.RED}Fail{Style.RESET_ALL}",
                    f"{exec_min_time}{constants.REPORT_MIN_UNIT} {exec_sec_time}{constants.REPORT_SECOND_UNIT}",
                    os.path.join(loopy_result_dir, "artifacts",
                                 index + "-" + role_name),
                ]
            )
            result_line += 1
    return table


def shorten_string(string, max_length):
    if len(string) <= max_length:
        return string
    else:
        return string[: max_length - 3] + "..."
