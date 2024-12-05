#!/usr/bin/env python
import sys
import os

# Define colors using ANSI escape codes
colors = {
    'dark_red': '\033[38;5;124m',
    'red': '\033[38;5;160m',
    'light_red': '\033[38;5;196m',
    'dark_green': '\033[38;5;154m',
    'green': '\033[38;5;155m',
    'light_green': '\033[38;5;156m',
    'dark_yellow': '\033[38;5;226m',
    'yellow': '\033[38;5;227m',
    'light_yellow': '\033[38;5;228m',
    'dark_purple': '\033[38;5;91m',
    'purple': '\033[38;5;92m',
    'light_purple': '\033[38;5;93m',
    'dark_sky': '\033[38;5;6m',
    'sky': '\033[38;5;12m',
    'light_sky': '\033[38;5;51m',
    'dark_blue': '\033[38;5;27m',
    'blue': '\033[38;5;33m',
    'light_blue': '\033[38;5;39m',
    'clear': '\033[0m',
    'color_reset': '\033[0m'
}

# Set log level colors
log_levels = {
    'info': colors['sky'],
    'debug': colors['light_sky'],
    'pending': colors['blue'],
    'warn': colors['dark_red'],
    'error': colors['red'],
    'fail': colors['light_red'],
    'die': colors['light_red'],
    'success': colors['light_green'],
    'pass': colors['green']
}

# Log functions with different severity levels

def die(message):
    print(f"{log_levels['die']}[FATAL]: {message}{colors['color_reset']}")
    sys.exit(1)

def debug(message, show_debug_log=True):
    if show_debug_log:
        print(f"{log_levels['debug']}[DEBUG] {message}{colors['color_reset']}")

def info(message):
    print(f"{log_levels['info']}[INFO] {message}{colors['color_reset']}")

def warn(message):
    print(f"{log_levels['warn']}[WARN] {message}{colors['color_reset']}")

def error(message):
    print(f"{log_levels['error']}[ERROR] {message}{colors['color_reset']}")

def fail(message):
    print(f"{log_levels['fail']}[FAIL] {message}{colors['color_reset']}")

def success(message):
    print(f"{log_levels['success']}[SUCCESS] {message}{colors['color_reset']}")

def pass_message(message):
    print(f"{log_levels['pass']}[PASS] {message}{colors['color_reset']}")

def pending(message):
    print(f"{log_levels['pending']}[PENDING] {message}{colors['color_reset']}")

def is_positive(input_string):
    input_string_lower="no"

    if input_string:
        input_string_lower = input_string.lower()       
    
    # return 0 when input is "yes", "true" 
    if input_string_lower in ["yes", "true"]:
        return 0
    # return 0 when input is "no", "false"
    elif input_string_lower in ["no", "false"]:
        return 1
    else:
        # return error if the input is something else
        raise ValueError("Invalid input. Please provide 'yes', 'no', 'true', or 'false'.")

def stop_when_error_happended(result, index_role_name, report_file, input_should_stop=False):
    if result != "0":
        warn(f"There are some errors in the role({index_role_name})")
        should_stop = is_positive(os.environ["STOP_WHEN_FAILED"])

        if input_should_stop:
            warn(f"Only for this role({index_role_name}) set 'STOP_WHEN_ERROR_HAPPENED' to {input_should_stop}")
            should_stop = is_positive(input_should_stop)

        if should_stop == 0:
            with open(report_file, 'a') as f:
                f.write(f"{index_role_name}::{result}\n")
            die(f"STOP_WHEN_ERROR_HAPPENED({should_stop}) is set and there are some errors detected, stopping all processes.")
        else:
            warn(f"STOP_WHEN_ERROR_HAPPENED({should_stop}) is NOT set, so skipping this error.")

def remove_comment_lines(command: str) -> str:
    lines = command.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("#")]
    return "\n".join(filtered_lines)
