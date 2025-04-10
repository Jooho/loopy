import json
import os

config_dict = {}

summary_dict = {}
config_file_path = "config.json"
summary_file_path = "summary.json"
abs_config_file_path = config_file_path
abs_summary_file_path = summary_file_path


def init_config(new_config):
    global abs_config_file_path
    global abs_summary_file_path
    config_dict.clear()
    config_dict.update(new_config)
    abs_config_file_path = os.path.join(new_config["loopy_root_path"], config_file_path)
    abs_summary_file_path = os.path.join(new_config["loopy_root_path"], summary_file_path)
    try:
        with open(abs_summary_file_path, "w") as file:
            file.write(str(summary_dict))
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

    try:
        with open(abs_config_file_path, "w") as file:
            file.write(str(config_dict))
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def update_config(key, value):
    config_dict[key] = value
    try:
        with open(abs_config_file_path, "w") as file:
            file.write(str(config_dict))
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def reset_config():
    config_dict = []
    try:
        with open(abs_config_file_path, "w") as file:
            file.write(str(config_dict))
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def update_summary(key, value):
    summary_dict[key] = value
    try:
        with open(abs_summary_file_path, "w") as file:
            json.dump(summary_dict, file)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def reset_summary():
    summary_dict = []
    try:
        with open(abs_summary_file_path, "w") as file:
            json.dump(summary_dict, file)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")


def load_summary():
    try:
        with open(abs_summary_file_path, "r") as file:
            data = json.load(file)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
    summary_dict.update(data)
