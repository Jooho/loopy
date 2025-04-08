# fmt: off
import os
import click
# import utils
import utils

import yaml
import constants
import loopy_report 
import logging
import logging.config
from component import Role, Get_default_input_value, Get_required_input_keys
from colorama import Fore, Style, Back
from core.context import get_context

context= get_context()
logger = logging.getLogger(__name__)

role_list = []
enable_loopy_log=True
enable_loopy_logo=True
enable_loopy_report=True

@click.pass_context
def init(ctx,verbose=None):
    global role_list
    global enable_loopy_log
    global enable_loopy_logo
    global enable_loopy_report
    if len(role_list) == 0:
        # Set log level
        logging_config = context["config"]["logging"]
        default_log_level=logging_config['handlers']['console']['level']
        
        log_levels = {
            1: logging.WARN,
            2: logging.INFO,
            3: logging.DEBUG
        }
        input_log_level=log_levels.get(verbose, default_log_level)
        logging_config['handlers']['console']['level']=input_log_level
        logging.config.dictConfig(logging_config)
        
        if input_log_level == logging.DEBUG:
             os.environ['SHOW_DEBUG_LOG']="true"

        # Enable Loopy Report
        # enable_loopy_report = ctx.obj.get("config", {}).get("config_data", {}).get("enable_loopy_report", [])
        enable_loopy_report = context["config"]["enable_loopy_report"]
        logger.debug(f"{constants.LOG_STRING_CONFIG}:enable_loopy_report: {enable_loopy_report}")
        
        # Enable Loopy Logo
        # enable_loopy_logo = ctx.obj.get("config", {}).get("config_data", {}).get("enable_loopy_logo", [])
        enable_loopy_logo = context["config"]["enable_loopy_logo"]
        logger.debug(f"{constants.LOG_STRING_CONFIG}:enable_loopy_logo: {enable_loopy_logo}")
        
        # Enable Loopy Log
        # enable_loopy_log = ctx.obj.get("config", {}).get("config_data", {}).get("enable_loopy_log", [])
        enable_loopy_log = context["config"]["enable_loopy_log"]
        logger.debug(f"{constants.LOG_STRING_CONFIG}:enable_loopy_log: {enable_loopy_log}")
        
        # Default Roles
        loopy_root_path = os.environ.get("LOOPY_PATH", "")
        default_roles_dir = f"{loopy_root_path}/default_provided_services/roles" if loopy_root_path else "./default_provided_services/roles"
        
        # Additional Roles
        # additional_role_dirs = ctx.obj.get("config", {}).get("config_data", {}).get("additional_role_dirs", [])
        additional_role_dirs = context["config"]["additional_role_dirs"]
        logger.debug(f"{constants.LOG_STRING_CONFIG}:additional_role_dirs: {additional_role_dirs}")
        
        # Combine default and additional roles directories
        roles_dir_list = [default_roles_dir] + additional_role_dirs
        logger.debug(f"{constants.LOG_STRING_CONFIG}:roles_dir_list: {roles_dir_list}")
        
        # Initialize roles
        for directory in roles_dir_list:
            roles = utils.initialize(directory, "role")
            role_list.extend(roles)

@click.command(name="list")
def list_roles():
    init()
    click.echo("Available roles:")
    for role in sorted(role_list, key=lambda x: x["name"]):
        click.echo(f" - {role['name']}")

@click.command(name="show")
@click.argument("role_name")
@click.pass_context
def show_role(ctx, role_name):
    init()
    verify_role_exist(role_name)
  
    for item in role_list:
        if role_name == item["name"]:
            role_path=item["path"]
   
    display_role_info(ctx, role_name, role_path)
    

@click.command(name="test")
@click.argument("role_name")
def test_role(role_name):
    init()
    click.echo(f"Running tests for role: {role_name}")
    click.echo(f"THIS COMMAND is not implemented")
    # Add your implementation here

@click.command(name="run")
@click.argument("role_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-r", "--no-report", is_flag=True)
@click.option("-l", "--no-logo", is_flag=True)
@click.option("-g", "--no-log", is_flag=True)
@click.option('-v', '--verbose', count=True)
@click.option("-o", "--output-env-file-name")
@click.option("-i", "--input-env-file")
@click.pass_context
def run_role(ctx, role_name, no_report, no_logo, no_log, verbose, params=None, output_env_file_name=None, input_env_file=None):   
    init(verbose)
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_log: {no_log}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_logo: {no_logo}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_report: {no_report}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:verbose: {verbose}")    
    
    # Enable loopy role log
    if no_log:
        os.environ['ENABLE_LOOPY_LOG']="false"
    elif enable_loopy_log:
        os.environ['ENABLE_LOOPY_LOG']="true"
    else:
        os.environ['ENABLE_LOOPY_LOG']="false"
        
    # Print logo    
    if no_logo:
       pass
    elif enable_loopy_logo:
        utils.print_logo()
    else:
        pass
        
    # role command specific validation
    verify_role_exist(role_name)
    verify_if_param_exist_in_role(ctx, params, role_name)
        
    # Params is priority. additional vars will be overwritten by params
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)           
    params=utils.update_params_with_input_file(additional_vars_from_file,params)    

    role = Role(ctx, None, role_list, role_name, params, output_env_file_name,None)
    role.start()
    
    # Print report
    if no_report:
        pass
    elif enable_loopy_report:
        loopy_report.summary(ctx, "role", None,None)
    else:
        pass
    
def verify_role_exist(role_name):
    for item in role_list:
        if role_name == item["name"]:
            return    
    logger.error(f"Role name({role_name}) does not exist")
    exit(1)


def verify_if_param_exist_in_role(ctx, params, role_name):
    if not params:
        return
    input_exist = False
    target_param = None
    for role in role_list:
        if role_name == role["name"]:
            role_config_path = role["path"] + "/config.yaml"
            with open(role_config_path, "r") as file:
                role_vars = yaml.safe_load(file)
                for param in params:
                    target_param = param
                    for role_config_env in role_vars["role"]["input_env"]:
                        if str.lower(role_config_env["name"]) == str.lower(param):
                            input_exist = True
                            break
                        else:
                            input_exist = False
                            
    # ignore_validate_env_input = ctx.obj.get("config", "config_data")["config_data"]["ignore_validate_env_input"]
    ignore_validate_env_input = context["config"]["ignore_validate_env_input"]
    if input_exist:
        return
    elif ignore_validate_env_input:
        return
    else:
        logger.error(f"no input enviroment name exist:{Back.BLUE} {target_param}")
        exit(1)


def display_role_info(ctx, role_name,role_path):
    role_config_data=utils.get_config_data_by_config_file_dir(ctx, role_path)['role']
    target_main_file=os.path.join(role_path,"main.sh")
    if not os.path.exists(target_main_file):
        target_main_file=os.path.join(role_path,"main.py")
    
    click.echo(f"{Fore.BLUE}Type:{Style.RESET_ALL} Role")
    click.echo(f"{Fore.BLUE}Name:{Style.RESET_ALL} {role_name}")
    click.echo(f"{Fore.BLUE}Description:{Style.RESET_ALL} {role_config_data.get('description','')}")
    click.echo(f"{Fore.BLUE}Main File Path:{Style.RESET_ALL} {target_main_file}")
    click.echo(f"{Fore.BLUE}Example Command:{Style.RESET_ALL}{Fore.RED} loopy role run {role_name}{Style.RESET_ALL}")

    input_env_list= role_config_data.get('input_env', {})
    output_env_list= role_config_data.get('output_env', {})
         
    click.echo(f"{Fore.BLUE}Input:{Style.RESET_ALL}{' '*51}| {Fore.BLUE}Output:{Style.RESET_ALL}")
    click.echo(f"- {Fore.GREEN}required{Style.RESET_ALL}{' '*(57-len('- required'))}| - {Fore.GREEN}required{Style.RESET_ALL}")
    required_input_keys = Get_required_input_keys(ctx, role_path, role_name)
    required_input_output_max_len = max(len(required_input_keys), len(output_env_list))
    
    for i in range(required_input_output_max_len):
        input_env = required_input_keys[i] if i < len(required_input_keys) else {}
        output_env = output_env_list[i] if i < len(output_env_list) else {}
        input_name = input_env
        output_name = output_env.get('name', '')
        default_input_value = Get_default_input_value(ctx, role_path, role_name, None, input_name) if input_name else ''
        if input_name and output_name:
           click.echo(f"  - {input_name} ({default_input_value}) {' '*(48-len(input_name) - len(default_input_value))} |   - {output_name}")
        elif input_name and not output_name:
           click.echo(f"  - {input_name} ({default_input_value}) {' '*(48-len(input_name) - len(default_input_value))} | ")
        elif not input_name and output_name:
           click.echo(f" {' '*(55)} |   - {output_name}")
   
    click.echo(f"- {Fore.YELLOW}optional{Style.RESET_ALL}{' '*(57-len('- optional'))}| - {Fore.YELLOW}optional{Style.RESET_ALL}")
    for input in input_env_list:
        input_name=input['name']
        if not input_name in required_input_keys:
            default_input_value = Get_default_input_value(ctx, role_path, role_name, None, input_name) if input_name else ''
            if len(default_input_value)> 55:
                click.echo(f"  - {input_name}  {' '*(50-len(input_name) )} | ")
                click.echo(f"    ({default_input_value}) {' '*(48- len(default_input_value))} ")
            else:                    
                click.echo(f"  - {input_name} ({default_input_value}) {' '*(48-len(input_name) - len(default_input_value))} | ")
