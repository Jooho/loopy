import os
import re


def find_root_directory(cur_dir):
    while not os.path.isdir(os.path.join(cur_dir, ".git")) and cur_dir != "/":
        cur_dir = os.path.dirname(cur_dir)
    if os.path.isdir(os.path.join(cur_dir, ".git")):
        return cur_dir
    else:
        return None


current_dir = os.path.dirname(os.path.abspath(__file__))
Root_directory = find_root_directory(current_dir)
