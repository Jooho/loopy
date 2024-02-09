import subprocess
import os
import yaml
import utils
from config import config_dict

class Role:
    def __init__(self, ctx, index, default_vars, role_list, role_name, params, param_output_env_file):
        self.index=index
        self.name = role_name
        self.default_vars = default_vars
        self.role_config_dir_path = get_role_config_dir_path(role_list, role_name)
        self.params = params
        self.ctx = ctx
        self.param_output_env_file=param_output_env_file
            
    def start(self,additional_input_vars=None):        
        output_env_dir_path=config_dict['output_dir']
        artifacts_dir_path=config_dict['artifacts_dir']
        if self.index is not None:
            role_dir_name= f"{self.index}-{self.name}"
            role_dir_path=os.path.join(artifacts_dir_path,role_dir_name)
        else:
            role_dir_path=os.path.join(artifacts_dir_path,self.name)                        
        create_dir_if_does_not_exist(role_dir_path)        
        os.environ['ROLE_DIR']=role_dir_path
        
        print(f"Role '{self.name}': Gathering environment and setting environment variables")
        gather_env(
            self.ctx,
            self.default_vars,
            self.role_config_dir_path,
            self.name,
            self.params,
            additional_input_vars
        )
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
            with open(log_output_file, 'w') as f:
                with subprocess.Popen(['bash', self.role_config_dir_path + "/main.sh"], stdout=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True) as proc:                
                    for line in proc.stdout:
                        print(line, end='') 
                        f.write(line)
        except subprocess.CalledProcessError as e:
            print(f"Command failed with return code {e.returncode}:")
            print(e.output)
        
        print(f"Role '{self.name}': Validating output file with specific environment variables")
        validate_output_env_file(output_env_file_full_path,self.role_config_dir_path)
        print(f'Finished role "{self.name}"')
        print()

class Unit:
    def __init__(self, unit_name,role, unit_input_env):
        self.name = unit_name
        self.role=role
        self.unit_input_env= unit_input_env

    def start(self):
        print(f"Unit '{self.name}': Starting role '{self.role.name}'")
        self.role.start(self.unit_input_env)


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
    

def gather_env(ctx, default_vars, role_config_dir_path, role_name, params,additional_input_vars):
    required_envs = []
    # Set them as environment variables
    role_group_name=role_name.split("-")[0]
    for key in default_vars[role_group_name]:
        os.environ[str.upper(key)] = default_vars[role_group_name][key]

    # Load config.yaml in the role. Read input_env and overwrite the environment value if there is default field
    with open(role_config_dir_path+"/config.yaml", "r") as file:
        role_config_vars = yaml.safe_load(file)
        for role_config_input_env in role_config_vars["role"]["input_env"]:
            # print(role_config_input_env)
            for role_default_env in role_config_input_env:
                if "required" in role_default_env:
                    required_envs.append(role_config_input_env["name"])
                if "default" in role_default_env:
                    os.environ[role_config_input_env["name"]] = role_config_input_env["default"]
                    
                        
    # If it is unit, add additional input variabels
    if additional_input_vars is not None:
        for input_var in additional_input_vars:
            os.environ[input_var] = additional_input_vars[input_var]
            
    # If user put params, it will overwrite environment variable
    with open(role_config_dir_path+"/config.yaml", "r") as file:
        role_config_vars = yaml.safe_load(file)
        for param in params:
            for role_config_input_env in role_config_vars["role"]["input_env"]:
                if str.lower(role_config_input_env["name"]) == str.lower(param):
                    os.environ[role_config_input_env["name"]] = params[param]
    verify_required_env_exist(required_envs)


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
                    target_output_file_path=f"{index}.{target_component_vars['role']['output_filename']}"
                else:
                    target_output_file_path=target_component_vars["role"]["output_filename"]
                
        if param_output_env_file is not None:
            target_output_file_path=param_output_env_file
        else:
            if index is not None:
                target_output_file_path=f"{index}.{target_component_vars['role']['name']}-output.sh"
            else:                
                target_output_file_path=target_component_vars["role"]["name"] +"-output.sh"
    return output_dir+"/"+ target_output_file_path

    
