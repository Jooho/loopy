import os
import utils
from colorama import Fore, Style
from config import summary_dict, load_summary
from prettytable import PrettyTable
import constants


def summary(ctx, type, config_data, unit_list):
    load_summary()
    summary_text = ["╦  ╔═╗╔═╗╔═╗╦ ╦", "║  ║ ║║ ║╠═╝╚╦╝", "╩═╝╚═╝╚═╝╩   ╩ ", "╔═╗┬ ┬┌┬┐┌┬┐┌─┐┬─┐┬ ┬", "╚═╗│ │││││││├─┤├┬┘└┬┘", "╚═╝└─┘┴ ┴┴ ┴┴ ┴┴└─ ┴ "]
    first_component_type = summary_dict["first_component_type"]
    first_component_name = summary_dict["first_component_name"]
    loopy_result_dir = summary_dict["loopy_result_dir"]
    start_time = summary_dict["start_time"]
    end_time = summary_dict["end_time"]

    execution_time = end_time[-1] - start_time[0]
    total_minutes = int(execution_time // 60)
    total_seconds = round(float(execution_time % 60), constants.REPORT_EXECUTION_TIME_ROUND)

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
        print("* " + " " * padding_length + line + " " * (max_line_length - len(line) - padding_length) + " *")
    # Print additional info
    for info in additional_info:
        padding_length = (max_line_length - len(info)) // 2
        key = info.split(":")[0].strip()
        value = info.split(":")[1].strip()
        new_string = f"{Fore.BLUE}{key}{Fore.RESET}" + ":" + f"{Fore.YELLOW} {value}{Fore.RESET}"

        print("* " + " " * padding_length + new_string + " " * (max_line_length - len(info) - padding_length) + " *")

    # Print bottom border
    print("*" * (max_line_length + 4))

    # Report Table
    report_file = os.path.join(summary_dict["loopy_result_dir"], "report")

    # Execution time per role
    execution_time_min_list = [int((end - start) // 60) for start, end in zip(start_time, end_time)]
    execution_time_sec_list = [round(float((end - start) % 60), constants.REPORT_EXECUTION_TIME_ROUND) for start, end in zip(start_time, end_time)]

    # When it is shell-execute role, it can have multiple times,
    # Then it needs to accumulate the times to show full execution time
    execution_time_min_list, execution_time_sec_list = accumulate_time_per_role(report_file, execution_time_min_list, execution_time_sec_list)

    table = PrettyTable(["Index", "Role Name", "Result", "Time", "Folder"])
    if type == "playbook":
        table = get_report_table_for_playbook(ctx, table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data, unit_list)
    else:
        table = get_report_table_for_unit_role(table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data)
    print(table)


def getDescription(ctx, role_name, step_index, to_check_duplicate_role_name, py_config_data, unit_list):
    description = ""
    steps = py_config_data["playbook"]["steps"]

    step = steps[step_index]
    if "unit" in step:
        unit_name = step["unit"]["name"]
        unit_config_data = utils.get_config_data_by_name(ctx, unit_name, "unit", unit_list)
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
    target_index_list = []
    temp_execution_time_min_list = []
    temp_execution_time_sec_list = []

    with open(f"{report_file}", "r") as file:
        data = file.readlines()
        prev_role_index = "-1"
        prev_role_name = ""
        target_index = None
        time_index = 0
        same_role_count = 0
        total_min_time = 0
        total_sec_time = 0.0

        for line in data:
            line = line.strip()  # Delete enter
            if not line or line.startswith("#"):  # Skip # part
                continue

            # if it has index, it is units
            if line[0].isdigit():
                role_index, report_data = line.split("-", 1)
            else:
                role_index = "0"
                report_data = line

            result_data = report_data.split("::")  # separate data by "::""
            role_name = result_data[0]

            # Accumulate times per role
            if prev_role_index == role_index and prev_role_name == role_name:
                target_index = time_index
                total_min_time += execution_time_min_list[int(target_index) + temp_index]
                total_sec_time += round(execution_time_sec_list[int(target_index) + temp_index], constants.REPORT_EXECUTION_TIME_ROUND)
                temp_index += 1
                same_role_count += 1

            else:
                # Add accumualted time
                if total_sec_time != 0 and target_index != None:
                    temp_execution_time_min_list.append(total_min_time)
                    temp_execution_time_sec_list.append(round(total_sec_time, constants.REPORT_EXECUTION_TIME_ROUND))
                    target_index_list.append(target_index)
                    total_min_time = 0
                    total_sec_time = 0

                # Move time list index when there were same index/role_name
                if same_role_count != 0:
                    time_index = time_index + same_role_count
                # If role index is changed, move time list index(except the first component)
                else:
                    if prev_role_index != role_index:
                        if prev_role_index != "-1":
                            time_index += 1

                # To check, the result has more result with the same role
                prev_role_index = role_index
                prev_role_name = role_name
                # Reset variables fo next role
                temp_index = 0
                same_role_count = 0

        #  if there is no more result to load, it will check the last role was doing accumulating execution time
        if total_sec_time != 0 and target_index != None:
            temp_execution_time_min_list.append(total_min_time)
            temp_execution_time_sec_list.append(round(total_sec_time, constants.REPORT_EXECUTION_TIME_ROUND))
            target_index_list.append(target_index)

    for index, i in enumerate(reversed(target_index_list)):
        insert_index = int(i)
        execution_time_min_list.insert(insert_index, temp_execution_time_min_list[len(target_index_list) - (index + 1)])
        execution_time_sec_list.insert(insert_index, temp_execution_time_sec_list[len(target_index_list) - (index + 1)])
    return execution_time_min_list, execution_time_sec_list


def get_report_table_for_unit_role(table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data):
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
            if type == "unit":
                steps = config_data[type]["steps"]
                if "description" in steps[int(index)]["role"]:
                    description = shorten_string(steps[int(index)]["role"]["description"], constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH)

            table.add_row(
                [
                    final_index.strip(),
                    description if description != "" else role_name.strip(),
                    f"{Fore.GREEN}Success{Fore.RESET}" if result.strip() == "0" else f"{Fore.RED}Fail{Fore.RESET}",
                    f"{exec_min_time}{constants.REPORT_MIN_UNIT} {exec_sec_time}{constants.REPORT_SECOND_UNIT}",
                    os.path.join(loopy_result_dir, "artifacts", index + "-" + role_name),
                ]
            )
            result_line += 1
    return table


def get_report_table_for_playbook(ctx, table, type, report_file, execution_time_min_list, execution_time_sec_list, loopy_result_dir, config_data, unit_list):
    py_steps = config_data["playbook"]["steps"]
    py_step_unit_role_description = []
    py_step_time_position_index_list = []
    py_step_min_time_list = []
    py_step_sec_time_list = []
    target_index = 0
    for step in py_steps:
        temp_min_time = 0
        temp_sec_time = 0.0
        if "unit" in step:
            unit_name = step["unit"]["name"]
            if "description" in step["unit"]:
                py_step_unit_role_description.append(step["unit"]["description"])
            else:
                py_step_unit_role_description.append(unit_name)
            unit_config_data = utils.get_config_data_by_name(ctx, unit_name, type, unit_list)
            unit_steps = unit_config_data["unit"]["steps"]
            command_count = 0
            py_step_time_position_index_list.append(target_index)
            for role in unit_steps:
                if "shell-execute" == role["role"]["name"]:
                    commands_list = role["role"]["input_env"]["COMMANDS"].split("%%")
                    for command in commands_list:
                        if command.strip() != '':
                            command_count+=1
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
            if "description" in step["role"]:
                py_step_unit_role_description.append(step["role"]["description"])
            else:
                py_step_unit_role_description.append(step["role"]["name"])
            py_step_time_position_index_list.append(target_index)
            command_count = 0
            if "shell-execute" == step["role"]["name"]:
                commands_list = step["role"]["input_env"]["COMMANDS"].split("%%")
                for command in commands_list:
                    if command.strip() != '':
                        command_count+=1
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
                    accumulate_time_index_per_unit_role = py_step_time_position_index_list.index(result_line)
                    to_check_duplicate_role_name = 0
                else:
                    to_check_duplicate_role_name += 1

                description = shorten_string(
                    getDescription(ctx, role_name, accumulate_time_index_per_unit_role, to_check_duplicate_role_name, config_data, unit_list), constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH
                )

            if result_line in py_step_time_position_index_list:
                accumulate_time_index_per_unit_role = py_step_time_position_index_list.index(result_line)
                unit_description = shorten_string(py_step_unit_role_description[accumulate_time_index_per_unit_role], constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH)
                table.add_row(
                    [
                        f"{Fore.YELLOW}Step({accumulate_time_index_per_unit_role})",
                        f"{unit_description}",
                        f"\u21A7",
                        f"{py_step_min_time_list[accumulate_time_index_per_unit_role]}{constants.REPORT_MIN_UNIT} {round(py_step_sec_time_list[accumulate_time_index_per_unit_role],constants.REPORT_EXECUTION_TIME_ROUND)}{constants.REPORT_SECOND_UNIT}{Fore.RESET}",
                        "",
                    ]
                )

            table.add_row(
                [
                    f"R({final_index.strip()})",
                    description if description != "" else role_name.strip(),
                    f"{Fore.GREEN}Success{Fore.RESET}" if result.strip() == "0" else f"{Fore.RED}Fail{Fore.RESET}",
                    f"{exec_min_time}{constants.REPORT_MIN_UNIT} {exec_sec_time}{constants.REPORT_SECOND_UNIT}",
                    os.path.join(loopy_result_dir, "artifacts", index + "-" + role_name),
                ]
            )
            result_line += 1
    return table


def shorten_string(string, max_length):
    if len(string) <= max_length:
        return string
    else:
        return string[: max_length - 3] + "..."
