# fmt: off
import os
import click
from cli.commands import utils
from cli.commands import constants
from cli.commands import loopy_report

import logging

from cli.logics.component import Role, Get_default_input_value, Get_required_input_keys
from colorama import Fore, Style, Back
from core.context import get_context

context= get_context()
logger = logging.getLogger(__name__)

role_list = context["config"]["role_list"]
enable_loopy_log=context["config"]["enable_loopy_log"]
enable_loopy_logo=context["config"]["enable_loopy_logo"]
enable_loopy_report=context["config"]["enable_loopy_report"]

@click.pass_context
def init(ctx,verbose=None):

    input_log_level=utils.configure_logging(context, verbose)
    if input_log_level == logging.DEBUG:
         os.environ['SHOW_DEBUG_LOG']="true"
        
    # Additional Roles
    additional_role_dirs = context["config"]["additional_role_dirs"]
    logger.debug(f"{constants.LOG_STRING_CONFIG}:additional_role_dirs: {additional_role_dirs}")        

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
    utils.verify_component_exist(role_name, role_list, "role")
  
    for item in role_list:
        if role_name == item["name"]:
            role_path=item["path"]
            break
   
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
    utils.verify_component_exist(role_name, role_list, "role")
    utils.verify_param_in_component(ctx,params, role_name, role_list, "role")
        
    # Params is priority. additional vars will be overwritten by params
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)           
    params=utils.update_params_with_input_file(additional_vars_from_file,params)  
    role_config    = utils.get_config_data_by_name(ctx, role_name, "role", role_list)
    role_description= role_config.get('description','')
    role = Role(ctx, None, role_list, role_name, role_description, params, output_env_file_name,None)
    role.start()
    
    # Print report
    if no_report:
        pass
    elif enable_loopy_report:
        loopy_report.summary(ctx, "role", None,None)
    else:
        pass

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
