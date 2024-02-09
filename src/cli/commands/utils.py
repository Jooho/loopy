import os
import yaml

def initialize(directory, type):
    item_list = []

    for root, dirs, files in os.walk(directory):
        if "config.yaml" in files:
            config_path = os.path.join(root, "config.yaml")
            with open(config_path, "r") as config_file:
                config_data = yaml.safe_load(config_file)
                if config_data:
                    if type == "role":
                        name = config_data["role"]["name"]
                        path = os.path.abspath(root)
                        item_list.append({"name": name, "path": path})
                    if type == "unit":
                        name = config_data["unit"]["name"]
                        role_name = config_data["unit"]["role"]["name"]
                        path = os.path.abspath(root)
                        item_list.append({"name": name, "path": path, "role_name": role_name})                        
                    if type == "playbook":
                        name = config_data["playbook"]["name"]
                        path = os.path.abspath(root)
                        item_list.append({"name": name, "path": path})                                                
    return item_list


def get_default_vars(ctx):
    return ctx.obj.get('config','default_vars') ["default_vars"] 
    
    
def parse_key_value_pairs(ctx, param, value):
    if value is None:
        return {}

    result = {}
    for item in value:
        key, value = item.split('=')
        result[key] = value

    return result
    

def load_env_file_if_exist(file):
    additional_vars = {}
    if file is not None:
        if os.path.exists(file):
            with open(file, "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    # os.environ[key] = value
                    additional_vars[key]=value
        else:
            print(f"File({file}) does not exist")
            exit(1)
    return additional_vars 

def set_env_vars_if_file_exist(file):
    if file is not None:
        if os.path.exists(file):
            with open(file, "r") as file:
                for line in file:
                    key, value = line.strip().split("=")
                    os.environ[key] = value

def update_params_with_input_file(additional_vars_from_file,params):
    updated_params=params
    if len(additional_vars_from_file) != 0:
        for key, value in params.items():
            additional_vars_from_file[key] = value  
        updated_params=additional_vars_from_file
    return updated_params
