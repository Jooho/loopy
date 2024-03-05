import subprocess
import os
import yaml
import utils
from config import config_dict, update_config

class Role:
    def __init__(self, ctx, index, role_list, role_name, params, param_output_env_file,additional_input_vars=None):
        self.index=index
        self.name = role_name
        self.role_config_dir_path = get_role_config_dir_path(role_list, role_name)
        self.params = params
        self.ctx = ctx
        self.param_output_env_file=param_output_env_file
        self.additional_input_vars=additional_input_vars
            
    def start(self):        
        output_env_dir_path=config_dict['output_dir']
        artifacts_dir_path=config_dict['artifacts_dir']
        if self.index is not None:
            role_dir_name= f"{self.index}-{self.name}"
            role_dir_path=os.path.join(artifacts_dir_path,role_dir_name)
        else:
            role_dir_path=os.path.join(artifacts_dir_path,self.name)                        
        create_dir_if_does_not_exist(role_dir_path)        
        os.environ['ROLE_DIR']=role_dir_path
        update_config('role_dir', role_dir_path) 
        
        print(f"Role '{self.name}': Gathering environment and setting environment variables")
        aggregated_input_vars, required_envs=get_aggregated_input_vars(
            self.ctx,
            self.role_config_dir_path,
            self.name,
            self.params,
            self.additional_input_vars
        )        
        export_env_variables(aggregated_input_vars)
        verify_required_env_exist(required_envs)
        print(f"Role '{self.name}': Executing bash script")
        log_output_file=os.path.join(role_dir_path,"log")
        output_env_file_full_path=get_output_env_file_path(self.index,output_env_dir_path,self.role_config_dir_path,self.param_output_env_file)
        os.environ["OUTPUT_ENV_FILE"]=output_env_file_full_path
        try:
            # # TO-DO This does not show logs but save it to file
            # with open(log_output_file, "w") as log_file:    
            #     proc=subprocess.run(['bash', self.role_config_dir_path + "/main.sh"],capture_output=True,text=True, check=True)
            #     log_file.write(proc.stdout)
            # print(proc.stdout.strip())
            
            # This show logs and also save it to file
            target_main_file_type="bash"
            target_main_file=os.path.join(self.role_config_dir_path,"main.sh")
            if not os.path.exists(target_main_file):
                target_main_file=os.path.join(self.role_config_dir_path,"main.py")
                target_main_file_type="python"
            with open(log_output_file, 'w') as f:
                with subprocess.Popen([target_main_file_type, target_main_file], stdout=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True) as proc:                
                    for line in proc.stdout:
                        print(line, end='') 
                        f.write(line)
                # with subprocess.Popen(['bash', self.role_config_dir_path + "/main.sh"], stdout=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True) as proc:                
                #     for line in proc.stdout:
                #         print(line, end='') 
                #         f.write(line)                        
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}:")
            print(e.output)
        
        print(f"Role '{self.name}': Validating output file with specific environment variables")
        validate_output_env_file(output_env_file_full_path,self.role_config_dir_path)
        print(f'Finished role "{self.name}"')
        print()

class Unit:
    def __init__(self, unit_name):
        self.name = unit_name
        self.components = []
    
    def add_component(self, role):
        self.components.append(role)

    def start(self):
        print(f"Unit '{self.name}': Starting role")        
        for component in self.components:
            component.start()
class Playbook:
    def __init__(self, name):
        self.name = name
        self.components = []

    def add_component(self, component):
        self.components.append(component)

    def start(self):
        print()
        print(f"Playbook '{self.name}': Starting components")
        for component in self.components:
            component.start()

def create_dir_if_does_not_exist(directory_path):
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            print(f"Succeed to create a new direcotry: {directory_path}")
        except OSError as e:
            print(f"Failed to create a new direcotry: {directory_path} ({e})")
    

def export_env_variables(input_variabels):
    if 'STOP_WHEN_FAILED' not in input_variabels:
        # Set default value of stop_when_failed when it is not specified in the role/unit input_env or params
        os.environ["STOP_WHEN_FAILED"] = config_dict["stop_when_failed"]

    for input_var in input_variabels:
        os.environ[input_var] = input_variabels[input_var]

def Get_default_input_value(ctx, role_config_dir_path, role_name, additional_input_vars, input_key):
    aggregated_input_vars, _ = get_aggregated_input_vars(ctx,role_config_dir_path,role_name, None, additional_input_vars)
        
    if input_key in aggregated_input_vars:
       return  aggregated_input_vars[input_key]      
   
    return ""

def Get_required_input_keys(ctx, role_config_dir_path, role_name):
    _, required_envs = get_aggregated_input_vars(ctx,role_config_dir_path,role_name, None, None)
    
    return required_envs


def get_aggregated_input_vars(ctx, role_config_dir_path, role_name, params, additional_input_vars):
    default_vars = utils.get_default_vars(ctx)
    required_envs = []
    aggregated_input_vars = {}

    role_group_name=role_name.split("-")[0]
    for key in default_vars.get(role_group_name, {}): 
        aggregated_input_vars[str.upper(key)] = default_vars[role_group_name][key]
        
    # Load config.yaml in the role. Read input_env and overwrite the environment value if there is default field
    with open(role_config_dir_path + "/config.yaml", "r") as file:
        role_config_vars = yaml.safe_load(file)
        for input_env in role_config_vars["role"]["input_env"]:
            for default_env in input_env:
                if "required" in default_env:
                    required_envs.append(input_env["name"])
                if "default" in default_env:
                    aggregated_input_vars[input_env["name"]] = input_env["default"]

    # If it is unit, add additional input variables
    if additional_input_vars is not None:
        for input_var, value in additional_input_vars.items():
            aggregated_input_vars[input_var] = value

    # If user put params, it will overwrite environment variable
    if params is not None:
        for param in params:
            for input_env in role_config_vars["role"]["input_env"]:
                if input_env["name"].lower() == param.lower():
                    aggregated_input_vars[input_env["name"]] = params[param]

    return aggregated_input_vars, required_envs

def verify_required_env_exist(required_envs):
    for required_env in required_envs:
        if required_env not in os.environ:
            print(f"Required environment value({required_env}) is not set")
            exit(1)

def validate_output_env_file(output_env_file_path,role_config_dir_path):
    with open(role_config_dir_path+"/config.yaml", "r") as file:
        target_component_vars = yaml.safe_load(file)
        utils.set_env_vars_if_file_exist(output_env_file_path)
        if "output_env" in target_component_vars["role"]:      
            for output_env in target_component_vars["role"]["output_env"]:             
                if str(output_env['name']) not in os.environ:
                    print(f"Please checkt this role. output_env({output_env}) is not set")
                    exit(1)
        else:
            return
        
def get_role_config_dir_path(role_list, role_name):
    target_config_yaml_dir_path = None
    for item in role_list:
        if role_name == item["name"]:
            target_config_yaml_dir_path = item["path"]
    if target_config_yaml_dir_path is None:
        print(f"role({role_name} does not exist)")        
        exit(1)
    return target_config_yaml_dir_path

def get_output_env_file_path(index,output_dir,role_config_dir_path,param_output_env_file):
    target_output_file_path=""
    with open(role_config_dir_path+"/config.yaml", "r") as file:
        target_component_vars = yaml.safe_load(file)
        if "output_env" in target_component_vars["role"]:            
            if "output_filename" in target_component_vars["role"]:
                if index is not None:
                    target_output_file_path=os.path.join(output_dir,f"{index}.{target_component_vars['role']['output_filename']}")
                else:
                    target_output_file_path=os.path.join(output_dir,target_component_vars["role"]["output_filename"])
                
        if param_output_env_file is not None:
            target_output_file_path=param_output_env_file
        else:
            if index is not None:
                target_output_file_path=os.path.join(output_dir,f"{index}.{target_component_vars['role']['name']}-output.sh")
            else:                
                target_output_file_path=os.path.join(output_dir,target_component_vars["role"]["name"] +"-output.sh")
    return target_output_file_path

    
