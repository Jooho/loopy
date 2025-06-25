import os
from colorama import Fore, Style
from core.report_manager import LoopyReportManager
from prettytable import PrettyTable
import constants


def summary(ctx):

    loopy_result_dir = ctx.obj.loopy_result_dir
    reportManager = LoopyReportManager(loopy_result_dir)
    reportManager.load_summary()
    report = os.path.join(loopy_result_dir, "report")
    report_lines = parse_report_file(report)

    components = reportManager.summary_dict["components"]
    first_component_type = reportManager.summary_dict["first_component_type"]

    update_results_from_report(reportManager, report_lines, components)
    flattened_components = flatten_components(components, [])

    print_report(
        ctx,
        reportManager,
        first_component_type,
        flattened_components,
        options={
            "show_index": True,
            "show_type": True,
            "show_name": True,
            "show_result": True,
            "show_time": True,
            "show_folder": True,
        },
    )


def print_report(ctx, reportManager, first_component_type, components, options=None):
    """
    Print the report in a formatted table.

    Args:
        components (list): List of components to be printed.
        options (dict): Options for printing, such as show_index, show_result, etc.
    """
    if options is None:
        options = {
            "show_index": True,
            "show_type": True,
            "show_name": True,
            "show_result": True,
            "show_time": True,
            "show_folder": True,
        }

    field_names = []
    if options["show_index"]:
        field_names.append("Index")
    if options["show_type"]:
        field_names.append("Type")
    if options["show_name"]:
        field_names.append("Role Name")
    if options["show_result"]:
        field_names.append("Result")
    if options["show_time"]:
        field_names.append("Time")
    if options["show_folder"]:
        field_names.append("Folder")

    table = PrettyTable(field_names)

    for i in range(len(components)):
        cur_component = components[i]

        if components[i].get("type") == "playbook":
            row = get_playbook_table_row(i, components[i], options)
            row = [str(cell).replace("\n", " ").strip() for cell in row]
            table.add_row(row)

        elif components[i].get("type") == "unit":
            row = get_unit_table_row(i, cur_component, options)
            row = [str(cell).replace("\n", " ").strip() for cell in row]
            table.add_row(row)
        else:
            row_list = get_role_table_row(
                i, cur_component, first_component_type, options
            )
            for row in row_list:
                table.add_row(row)

    playbook_execution_time = components[0].get("execution_time")
    loopy_summary_print(ctx, reportManager, playbook_execution_time)
    print(table)


def loopy_summary_print(ctx, reportManager, execution_time):
    print(f"{Fore.RESET}")  # Reset Color
    summary_text = [
        "╦  ╔═╗╔═╗╔═╗╦ ╦",
        "║  ║ ║║ ║╠═╝╚╦╝",
        "╩═╝╚═╝╚═╝╩   ╩ ",
        "╔═╗┬ ┬┌┬┐┌┬┐┌─┐┬─┐┬ ┬",
        "╚═╗│ │││││││├─┤├┬┘└┬┘",
        "╚═╝└─┘┴ ┴┴ ┴┴ ┴┴└─ ┴ ",
    ]
    first_component_type = reportManager.summary_dict["first_component_type"]
    first_component_name = reportManager.summary_dict["first_component_name"]
    loopy_result_dir = ctx.obj.loopy_result_dir
    execution_time, _ = format_time_and_result(execution_time, "")

    additional_info = [
        f"Run: {first_component_type}({first_component_name})",
        f"Loopy result dir: {loopy_result_dir}",
        f"Report file: {loopy_result_dir}/report",
        f"Execution time: {execution_time}",
    ]

    # Find the maximum length of text lines
    max_line_length = max(len(line) for line in summary_text) + 100

    # Print top border
    print("*" * (max_line_length + 4))

    # Print text with *
    for line in summary_text:
        padding_length = (max_line_length - len(line)) // 2
        print(
            "* "
            + " " * padding_length
            + line
            + " " * (max_line_length - len(line) - padding_length)
            + " *"
        )
    # Print additional info
    for info in additional_info:
        padding_length = (max_line_length - len(info)) // 2
        key = info.split(":")[0].strip()
        value = info.split(":")[1].strip()
        new_string = (
            f"{Fore.BLUE}{key}{Style.RESET_ALL}"
            + ":"
            + f"{Fore.YELLOW} {value}{Style.RESET_ALL}"
        )

        print(
            "* "
            + " " * padding_length
            + new_string
            + " " * (max_line_length - len(info) - padding_length)
            + " *"
        )

    # Print bottom border
    print("*" * (max_line_length + 4))


def get_playbook_table_row(index, component, options):
    """
    Get the table row for a playbook component.
    """
    description = shorten_string(
        (
            component.get("description")
            if component.get("description") not in (None, "")
            else component.get("name")
        ),
        constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH,
    )

    color = Fore.YELLOW
    row = []
    if options["show_index"]:
        row.append(f"{color}{index}{Style.RESET_ALL}")
    if options["show_type"]:
        row.append(f"{color}{component.get('type')}{Style.RESET_ALL}")
    if options["show_name"]:
        row.append(f"{color}{description}{Style.RESET_ALL}")
    if options["show_result"]:
        row.append(
            (
                f"{Style.RESET_ALL}{Fore.GREEN}Success{Style.RESET_ALL}"
                if component.get("result_str") == "Success"
                else f"{Fore.RED}Fail{Style.RESET_ALL}{Fore.YELLOW}"
            ),
        )
    if options["show_time"]:
        row.append(
            f"{color}{component.get('formatted_execution_time')}{Style.RESET_ALL}"
        )
    if options["show_folder"]:
        row.append("")

    return row


def get_unit_table_row(index, component, options):
    """
    Get the table row for a unit component.
    """
    description = shorten_string(
        (
            component.get("description")
            if component.get("description") not in (None, "")
            else component.get("name")
        ),
        constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH,
    )

    color = Fore.MAGENTA
    row = []
    if options["show_index"]:
        row.append(f"{color}{index}{Style.RESET_ALL}")
    if options["show_type"]:
        row.append(f"{color}{component.get('type')}{Style.RESET_ALL}")
    if options["show_name"]:
        row.append(f"{color}{description}{Style.RESET_ALL}")
    if options["show_result"]:
        row.append(
            f"{Style.RESET_ALL}{Fore.GREEN}Success{Style.RESET_ALL}{Fore.MAGENTA}"
            if component.get("result_str") == "Success"
            else f"{Fore.RED}Fail{Style.RESET_ALL}{Fore.MAGENTA}"
        ),
    if options["show_time"]:
        row.append(
            f"{color}{component.get('formatted_execution_time')}{Style.RESET_ALL}"
        )
    if options["show_folder"]:
        row.append("")

    return row


def get_role_table_row(index, component, first_component_type, options):
    """
    Get the table row for a playbook component.
    """
    description = shorten_string(
        (
            component.get("description")
            if component.get("description") not in (None, "")
            else component.get("name")
        ),
        constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH,
    )

    color = Fore.WHITE
    if first_component_type == "playbook":
        color = Fore.CYAN

    row_list = []
    row = []
    if options["show_index"]:
        row.append(f"{index}")
    if options["show_type"]:
        row.append(f"{component.get('type')}")
    if options["show_name"]:
        row.append(f"{description}")
    if options["show_result"]:
        row.append(
            f"{Style.RESET_ALL}{Fore.GREEN}Success{Style.RESET_ALL}{color}"
            if component.get("result_str") == "Success"
            else f"{Fore.RED}Fail{Style.RESET_ALL}{color}"
        ),
    if options["show_time"]:
        row.append(f"{component.get('formatted_execution_time')}")
    if options["show_folder"]:
        row.append(f"{component.get('artifacts_dir')}")

    # Apply color formatting
    row[0] = f"{color}" + row[0]
    row[-1] = row[-1] + f"{Style.RESET_ALL}"

    row_list.append(row)

    commands = component.get("commands")
    if len(commands) > 1:
        for i in range(len(commands)):
            row = get_command_table_row(
                index, i, commands[i], options, component.get("artifacts_dir")
            )
            row[-1] = row[-1]
            row_list.append(row)

    return row_list


def get_command_table_row(role_idx, index, component, options, artifacts_dir):
    """
    Get the table row for a command component.
    """
    description = shorten_string(
        (
            component.get("description")
            if component.get("description") not in (None, "")
            else component.get("name")
        ),
        constants.REPORT_MAXIMUM_DESCRIPTION_STRING_LENGTH,
    )
    formatted_time, result_str = format_time_and_result(
        component.get("execution_time"), component.get("result")
    )
    prefix = "*"

    color = Fore.BLUE
    row = []
    if options["show_index"]:
        row.append(f"{color}{role_idx}-{index}{Style.RESET_ALL}")
    if options["show_type"]:
        row.append(f"{color}{prefix} command{Style.RESET_ALL}")
    if options["show_name"]:
        row.append(f"{color}{description}{Style.RESET_ALL}")
    if options["show_result"]:
        row.append(
            f"{Style.RESET_ALL}{Fore.GREEN}Success{Style.RESET_ALL}{Fore.BLUE}"
            if result_str == "Success"
            else f"{Fore.RED}Fail{Style.RESET_ALL}{Fore.BLUE}"
        ),
    if options["show_time"]:
        row.append(f"{color}{formatted_time}{Style.RESET_ALL}")
    if options["show_folder"]:
        row.append(f"{color}{artifacts_dir}{Style.RESET_ALL}")

    return row


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


def flatten_components(component, flat_list, parent=None):
    info = {k: v for k, v in component.items() if k != "components"}

    # execution_time + result formatting
    if "execution_time" in component and "result" in component:
        formatted_time, result_str = format_time_and_result(
            component["execution_time"], component["result"]
        )
        info["formatted_execution_time"] = formatted_time
        info["result_str"] = result_str

    if parent:
        parent_type, parent_id_key, parent_id_val = parent
        info[f"parent_{parent_type}_{parent_id_key}"] = parent_id_val

    if "type" in info:
        flat_list.append(info)

    if "components" in component and isinstance(component["components"], list):
        curr_type = component.get("type")
        curr_id_key = "uuid"

        if curr_type and curr_id_key and curr_id_key in component:
            next_parent = (curr_type, curr_id_key, component[curr_id_key])
        else:
            next_parent = None

        for sub in component["components"]:
            flatten_components(sub, flat_list, parent=next_parent)

    return flat_list


def format_time_and_result(execution_time, result):
    seconds = execution_time
    minutes = int(seconds // 60)
    remaining_seconds = round(seconds % 60, 3)

    formatted_time = f"{minutes}min {remaining_seconds}"
    result_str = "Success" if result == 0 else "Fail"
    return formatted_time, result_str


def update_results_from_report(reportManager, report_lines, components):
    playbook_result = 0

    def update_role_result(components, role_index, role_name, role_results):
        if isinstance(components, list):
            for component in components:
                if update_role_result(component, role_index, role_name, role_results):
                    continue
        elif isinstance(components, dict):
            if "components" in components:
                return update_role_result(
                    components["components"], role_index, role_name, role_results
                )

            if components.get("type") == "role":
                if components.get("name") == role_name and str(
                    components.get("role_index")
                ) == str(role_index):
                    if len(components["commands"]) != len(role_results):
                        raise ValueError(
                            "length of commands and role_results is different"
                        )
                    for i in range(len(components["commands"])):
                        components["commands"][i]["result"] = int(role_results[i])
                        if components["commands"][i]["result"] == 1:
                            components["result"] = 1
                    return True

    def update_unit_result(unit):
        nonlocal playbook_result
        for role in unit["components"]:
            if "result" in role and role["result"] == 1:
                unit_result = 1
                unit["result"] = 1
                playbook_result = 1
                break

        return True

    def update_playbook_result(components):
        nonlocal playbook_result
        if isinstance(components, list):
            for component in components:
                if update_playbook_result(component):
                    continue
            return
        elif isinstance(components, dict):
            if components.get("type") == "playbook" and "components" in components:
                if update_playbook_result(components["components"]):
                    return

            if components.get("type") == "unit":
                return update_unit_result(components)

            if components.get("type") == "role":
                if components["result"] == 1:
                    playbook_result = 1
                    return True
                else:
                    return True

        components["result"] = playbook_result

    def parse_report_line(line):
        if line[0].isdigit():
            role_index, report_data = line.split("-", 1)
        else:
            role_index = 0
            report_data = line

        result_data = report_data.split("::")
        role_name = result_data[0]
        role_result = result_data[-1]
        return role_index, role_name, role_result

    def update_report_results(reportManager):
        role_results = []
        next_role_index = -1
        next_role_name = None

        for idx in range(len(report_lines)):
            role_index, role_name, role_result = parse_report_line(report_lines[idx])
            if idx != len(report_lines) - 1:
                next_role_index, next_role_name, _ = parse_report_line(
                    report_lines[idx + 1]
                )

            if role_index == next_role_index and role_name == next_role_name:
                role_results.append(role_result)
                next_role_index = -1
                next_role_name = None
                continue

            role_results.append(role_result)

            update_role_result(components, role_index, role_name, role_results)
            role_results = []
            next_role_index = -1
            next_role_name = None

        # for component in components:
        if components["type"] == "unit":
            update_unit_result(components)
        if components["type"] == "playbook":
            update_playbook_result(components)

        reportManager.load_summary()
        reportManager.update_summary("components", components)

    update_report_results(reportManager)


def shorten_string(string, max_length):
    if len(string) <= max_length:
        return string
    else:
        return string[: max_length - 3] + "..."
