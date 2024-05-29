# fmt: off
import os
import click
import utils
import yaml
import constants
import logging
import roles
import loopy_report 
from component import Role, Unit, Get_required_input_keys
from colorama import Fore, Style, Back

logger = logging.getLogger(__name__)

role_list = []
unit_list = []
enable_loopy_log=True
enable_loopy_logo=True
enable_loopy_report=True

@click.pass_context
def init(ctx, verbose=None):
    global role_list
    global unit_list
    global enable_loopy_log
    global enable_loopy_logo
    global enable_loopy_report
    
    # Set log level
    logging_config = ctx.obj.get("config", {}).get("config_data", {}).get("logging", [])
    default_log_level=logging_config['handlers']['console']['level']
    
    log_levels = {
        1: logging.WARN,
        2: logging.INFO,
        3: logging.DEBUG
    }

    logging_config['handlers']['console']['level']=log_levels.get(verbose, default_log_level)
    logging.config.dictConfig(logging_config)        
        
    # Enable Loopy Report
    enable_loopy_report = ctx.obj.get("config", {}).get("config_data", {}).get("enable_loopy_report", [])
    logger.debug(f"{constants.LOG_STRING_CONFIG}:enable_loopy_report: {enable_loopy_report}")
    
    # Enable Loopy Logo
    enable_loopy_logo = ctx.obj.get("config", {}).get("config_data", {}).get("enable_loopy_logo", [])
    logger.debug(f"{constants.LOG_STRING_CONFIG}:enable_loopy_logo: {enable_loopy_logo}")

    # Enable Loopy Log
    enable_loopy_log = ctx.obj.get("config", {}).get("config_data", {}).get("enable_loopy_log", [])
    logger.debug(f"{constants.LOG_STRING_CONFIG}:enable_loopy_log: {enable_loopy_log}")                
    
    # Default Roles/Units
    loopy_root_path = os.environ.get("LOOPY_PATH", "")
    default_roles_dir = f"{loopy_root_path}/src/roles" if loopy_root_path else "./src/roles"
    logger.debug(f"{constants.LOG_STRING_CONFIG}:default_roles_dir: {default_roles_dir}")
    default_units_dir = f"{loopy_root_path}/src/units" if loopy_root_path else "./src/units"
    logger.debug(f"{constants.LOG_STRING_CONFIG}:default_units_dir: {default_units_dir}")
    
    # Additional Roles/Units
    additional_role_dirs = ctx.obj.get("config", {}).get("config_data", {}).get("additional_role_dirs", [])
    logger.debug(f"{constants.LOG_STRING_CONFIG}:additional_role_dirs: {additional_role_dirs}")
    additional_unit_dirs = ctx.obj.get("config", {}).get("config_data", {}).get("additional_unit_dirs", [])
    logger.debug(f"{constants.LOG_STRING_CONFIG}:additional_unit_dirs: {additional_unit_dirs}")
    
    # Combine default and additional roles/units directories
    roles_dir_list = [default_roles_dir] + additional_role_dirs
    logger.debug(f"{constants.LOG_STRING_CONFIG}:roles_dir_list: {roles_dir_list}")
    units_dir_list = [default_units_dir] + additional_unit_dirs
    logger.debug(f"{constants.LOG_STRING_CONFIG}:units_dir_list: {units_dir_list}")
    
    # Initialize roles
    for directory in roles_dir_list:
        roles = utils.initialize(directory, "role")
        role_list.extend(roles)
    
    # Initialize units
    for directory in units_dir_list:
        units = utils.initialize(directory, "unit")
        unit_list.extend(units)
    
@click.command(name="list")
def list_units():
    init()
    click.echo("Available units:")
    for unit in sorted(unit_list, key=lambda x: x["name"]):
        click.echo(f" - {unit['name']}")

@click.command(name="show")
@click.argument("unit_name")
@click.option("-v", "--detail-information",is_flag=True)
@click.pass_context
def show_unit(ctx, unit_name,detail_information):   
    init() 
    verify_unit_exist(unit_name)
    
    for item in unit_list:
        if unit_name == item["name"]:
            unit_path = item["path"]
            role_name = item["role_name"]
    
    display_unit_info(ctx, unit_name, unit_path, role_name, detail_information)

@click.command(name="run")
@click.argument("unit_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-r", "--no-report", is_flag=True)
@click.option("-l", "--no-logo", is_flag=True)
@click.option("-g", "--no-log", is_flag=True)
@click.option('-v', '--verbose', count=True)
@click.option("-o", "--output-env-file-name")
@click.option("-i", "--input-env-file")
@click.pass_context
def run_unit(
    ctx, unit_name, no_report, no_logo, no_log, verbose, params=None, output_env_file_name=None, input_env_file=None
):
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_log: {no_log}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_logo: {no_logo}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_report: {no_report}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:verbose: {verbose}")    
    
    init(verbose)
    
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
    
    logger.info(f"Unit: {unit_name}")
    verify_unit_exist(unit_name)
    verify_if_param_exist_in_unit(ctx, params, unit_name, unit_list)

    # Params is priority. additional vars will be overwritten by params
    additional_vars_from_file = utils.load_env_file_if_exist(input_env_file)
    params = utils.update_params_with_input_file(additional_vars_from_file, params)

    # Create Unit component
    unit = Unit(unit_name)
    unit_config_data = utils.get_config_data_by_name(ctx, unit_name, "unit", unit_list)
    # print(f"step: {unit_config_data['unit']['steps']}")
    logger.debug(f"step: {unit_config_data['unit']['steps']}")
    
    # When Unit have multiple roles
    if "steps" in unit_config_data['unit']:
        for index, step in enumerate(unit_config_data['unit']["steps"]):
            #print(f"step: {step}")
            logger.debug(f"step: {step}")
            if list(step)[0] != "role":
                click.echo("Unit can not include another unit in the steps")
                exit(1)
            role_name = step["role"]["name"]
            additional_input_env = utils.get_input_env_from_config_data(step["role"])
            role = Role( ctx, index, role_list, role_name, params, None, additional_input_env )
            unit.add_component(role)
    # When Unit have single role(Deprecated)
    else:
        additional_input_env = utils.get_input_env_from_config_data( unit_config_data["role"] )
        role = Role( ctx, None, role_list, utils.get_first_role_name_in_unit_by_unit_name(unit_name, unit_list), params, output_env_file_name, additional_input_env )
        unit.add_component(role)
    unit.start()
    
    # Print report
    if no_report:
        pass
    elif enable_loopy_report:
        loopy_report.summary(ctx, "unit", unit_config_data,unit_list)
    else:
        pass


def verify_unit_exist(unit_name):
    for unit in unit_list:
        if unit_name == unit["name"]:
            return
    logger.error(f"Unit name({unit_name}) does not exist")    
    exit(1)

def verify_if_param_exist_in_unit(ctx, params, unit_name, unit_list):
    if not params:
        return
    for unit in unit_list:
        if unit_name == unit["name"]:
            unit_config_path = unit["path"] + "/config.yaml"
            with open(unit_config_path, "r") as file:
                unit_config_vars = yaml.safe_load(file)
                roles.verify_if_param_exist_in_role(ctx, params, unit_config_vars["unit"]["steps"][0]["role"]["name"])


def display_unit_info(ctx, unit_name, unit_path, role_name,detail_info):
    unit_config_data = utils.get_config_data_by_config_file_dir(ctx, unit_path)["unit"]
    for role in role_list:
        if role_name == role["name"]:
            role_path = role["path"]
    role_config_data = utils.get_config_data_by_config_file_dir(ctx, role_path)["role"]
    target_main_file = os.path.join(role_path, "main.sh")
    if not os.path.exists(target_main_file):
        target_main_file = os.path.join(role_path, "main.py")

    click.echo(f"{Fore.BLUE}Type:{Style.RESET_ALL} Unit")
    click.echo(f"{Fore.BLUE}Name:{Style.RESET_ALL} {unit_name}")
    click.echo( f"{Fore.BLUE}Description:{Style.RESET_ALL} {unit_config_data.get('description','')}" )
    click.echo(f"{Fore.BLUE}Unit Config File:{Style.RESET_ALL} {unit_path}/config.yaml")
    click.echo( f"{Fore.BLUE}Example Command:{Style.RESET_ALL}{Fore.RED} loopy units run {unit_name}{Style.RESET_ALL}" )
    click.echo(f"{Fore.BLUE}Unit Steps:{Style.RESET_ALL}")
    for step in unit_config_data["steps"]:       
        click.echo(f"{Fore.LIGHTYELLOW_EX}  -> {step['role']['name']}{Style.RESET_ALL}")
    
    if detail_info:
        click.echo(f"{Fore.BLUE}First Role:{Style.RESET_ALL}")
        click.echo(f"{Fore.BLUE}  Name:{Style.RESET_ALL} {role_name}")
        click.echo( f"{Fore.BLUE}  Description:{Style.RESET_ALL} {role_config_data.get('description','')}" )
        click.echo(f"{Fore.BLUE}  Main File Path:{Style.RESET_ALL} {target_main_file}")
        if "steps" in unit_config_data:
            unit_env_list = unit_config_data["steps"][0]["role"].get("input_env", {})
        else:
            unit_env_list = unit_config_data["role"].get("input_env", {})
        required_input_keys = Get_required_input_keys(ctx, role_path, role_name)

        click.echo(f"{Fore.BLUE}  Input:{Style.RESET_ALL}")
        no_value_keys = []
        for required_input_key in required_input_keys:
            if required_input_key in unit_env_list:
                unit_input_env = unit_env_list[required_input_key]
            else:
                no_value_keys.append(required_input_key)
                continue

            if unit_input_env:
                click.echo( f"  - {Fore.GREEN}{required_input_key:<20}:{Style.RESET_ALL} {unit_input_env}" )

        if len(no_value_keys) > 0:
            for no_value_key in no_value_keys:
                click.echo( f"  - {Fore.GREEN}{no_value_key:<20}:{Style.RESET_ALL} 'no specified'" )
