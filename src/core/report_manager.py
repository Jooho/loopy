import json
import os


class LoopyReportManager:
    def __init__(self, root_path="."):
        self.root_path = root_path
        self.summary_dict = {}
        self.role_time_dict = {"start_time": [], "end_time": []}
        self.summary_file_path = os.path.join(self.root_path, "summary.json")
        self.role_time_file_path = os.path.join(self.root_path, "role_time.json")

    def _write_to_file(self, file_path, data):
        try:
            with open(file_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"[ERROR] Failed to write to {file_path}: {e}")

    def _load_from_file(self, file_path):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Failed to load from {file_path}: {e}")
            return {}

    def init_report_data(self):
        self._write_to_file(self.summary_file_path, self.summary_dict)
        self._write_to_file(self.role_time_file_path, self.role_time_dict)

    def update_summary(self, key, value):
        self.summary_dict[key] = value
        self._write_to_file(self.summary_file_path, self.summary_dict)

    def reset_summary(self):
        self.summary_dict.clear()
        self._write_to_file(self.summary_file_path, self.summary_dict)

    def load_summary(self):
        self.summary_dict = self._load_from_file(self.summary_file_path)

    def update_role_time(self, key, value):
        self.role_time_dict[key] = value
        self._write_to_file(self.role_time_file_path, self.role_time_dict)

    def reset_role_time(self):
        self.role_time_dict = {"start_time": [], "end_time": []}
        self._write_to_file(self.role_time_file_path, self.role_time_dict)

    def load_role_time(self):
        self.role_time_dict = self._load_from_file(self.role_time_file_path)


# import json
# import os

# summary_dict = {}
# role_time_dict = {}


# summary_file_path = "summary.json"
# role_time_file_path = "role_time.json"
# abs_summary_file_path = summary_file_path
# abs_role_time_file_path = role_time_file_path


# def init_report(loopy_root_path):

#     global abs_summary_file_path
#     abs_summary_file_path = os.path.join(loopy_root_path, summary_file_path)
#     abs_role_time_file_path = os.path.join(loopy_root_path, role_time_file_path)
#     try:
#         with open(abs_summary_file_path, "w") as file:
#             file.write(str(summary_dict))
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")

#     try:
#         with open(abs_role_time_file_path, "w") as file:
#             file.write(str(role_time_dict))
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")

# def update_summary(key, value):
#     summary_dict[key] = value
#     try:
#         with open(abs_summary_file_path, "w") as file:
#             json.dump(summary_dict, file)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")


# def reset_summary():
#     summary_dict.clear()
#     try:
#         with open(abs_summary_file_path, "w") as file:
#             json.dump(summary_dict, file)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")


# def load_summary():
#     try:
#         with open(abs_summary_file_path, "r") as file:
#             data = json.load(file)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")
#     summary_dict.update(data)


# def update_role_time(key, value):
#     role_time_dict[key] = value
#     try:
#         with open(abs_role_time_file_path, "w") as file:
#             json.dump(role_time_dict, file)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")


# def reset_role_time():
#     role_time_dict.clear()
#     role_time_dict["start_time"] = []
#     role_time_dict["end_time"] = []

#     try:
#         with open(abs_role_time_file_path, "w") as file:
#             json.dump(role_time_dict, file)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")


# def load_role_time():
#     try:
#         with open(abs_role_time_file_path, "r") as file:
#             data = json.load(file)
#     except Exception as e:
#         print(f"[ERROR] Unexpected error: {e}")
#     role_time_dict.update(data)
