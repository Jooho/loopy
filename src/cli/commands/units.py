# fmt: off
import os
import click
import logging
from cli.commands import utils
from cli.commands import constants
from cli.commands import loopy_report
from cli.logics.component import Role, Unit, Get_required_input_keys
from colorama import Fore, Style
from core.report_manager import LoopyReportManager

logger = logging.getLogger(__name__)

@click.pass_context
def init(ctx, verbose=None):
    input_log_level=utils.configure_logging(ctx, verbose)
    if input_log_level == logging.DEBUG:
        os.environ['SHOW_DEBUG_LOG']="true"
    
    additional_role_dirs = ctx.obj.config["additional_role_dirs"]
    logger.debug(f"{constants.LOG_STRING_CONFIG}:additional_role_dirs: {additional_role_dirs}")
    
    additional_unit_dirs = ctx.obj.config["additional_unit_dirs"]
    logger.debug(f"{constants.LOG_STRING_CONFIG}:additional_unit_dirs: {additional_unit_dirs}")


@click.command(name="list")
@click.pass_context
def list_units(ctx):
    init()
    click.echo("Available units:")
    for unit in sorted(ctx.obj.unit_list, key=lambda x: x["name"]):
        click.echo(f" - {unit['name']}")

@click.command(name="show")
@click.argument("unit_name")
@click.option("-v", "--detail-information",is_flag=True)
@click.pass_context
def show_unit(ctx, unit_name,detail_information):   
    init() 
    unit_list=ctx.obj.unit_list
    utils.verify_component_exist(unit_name, unit_list, "unit")

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
    init(verbose)
    role_list=ctx.obj.role_list
    unit_list=ctx.obj.unit_list
    os.environ['ENABLE_LOOPY_LOG']=str(ctx.obj.config["enable_loopy_log"])
    enable_loopy_logo=ctx.obj.config["enable_loopy_logo"]
    enable_loopy_report=ctx.obj.config["enable_loopy_report"]    
    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_log: {no_log}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_logo: {no_logo}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:no_report: {no_report}")    
    logger.debug(f"{constants.LOG_STRING_CONFIG}:verbose: {verbose}")    


    # Enable loopy role log
    if no_log:
        os.environ['ENABLE_LOOPY_LOG']="false"

    # Print logo    
    if no_logo:
        pass
    elif enable_loopy_logo:
        utils.print_logo()
    else:
        pass

    logger.info(f"Unit: {unit_name}")
    
    utils.verify_component_exist(unit_name, unit_list, "unit")        
    utils.verify_param_in_component(ctx, params, unit_name, unit_list, "unit")

    # Params is priority. additional vars will be overwritten by params
    additional_vars_from_file = utils.load_env_file_if_exist(input_env_file)
    params = utils.update_params_with_input_file(additional_vars_from_file, params)

    reportManager = LoopyReportManager(ctx.obj.loopy_result_dir)
    reportManager.load_summary()
    reportManager.update_summary("first_component_type", "Unit")
    reportManager.update_summary("first_component_name", unit_name)
    # Create Unit component
    unit = Unit(ctx,unit_name)
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
            role_description = step["role"].get("description", "")
            additional_input_env = utils.get_input_env_from_config_data(step["role"])
            role = Role( ctx, index, role_list, role_name,role_description, params, None, additional_input_env )
            unit.add_component(role)
    # When Unit have single role(Deprecated)
    else:
        additional_input_env = utils.get_input_env_from_config_data( unit_config_data["role"] )
        role = Role(ctx, None, role_list, utils.get_first_role_name_in_unit_by_unit_name(unit_name, unit_list), role_description, params, output_env_file_name, additional_input_env )
        unit.add_component(role)
    unit.start()

    # Print report
    if no_report:
        pass
    elif enable_loopy_report:
        loopy_report.summary(ctx)
    else:
        pass

def display_unit_info(ctx, unit_name, unit_path, role_name,detail_info):
    unit_config_data = utils.get_config_data_by_config_file_dir(ctx, unit_path)["unit"]
    for role in ctx.obj.role_list:
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
