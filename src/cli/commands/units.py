import os 
import click
import utils
import yaml
import roles
from component import Role, Unit, Get_default_input_value, Get_required_input_keys
from colorama import Fore, Style, Back
unit_list=utils.initialize("./src/units", "unit")
role_list=utils.initialize("./src/roles", "role")

@click.command(name="list")
def list_units():
    click.echo("Available utils:")
    for unit in unit_list:
        click.echo(f" - {unit['name']}")

@click.command(name="show")
@click.argument("unit_name")
@click.pass_context
def show_unit(ctx, unit_name):
    verify_unit_exist(unit_name)  
    for item in unit_list:
        if unit_name == item["name"]:
            unit_path=item["path"]
            role_name=item["role_name"]
    display_unit_info(ctx, unit_name, unit_path, role_name)


@click.command(name="run")
@click.argument("unit_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-o", "--output-env-file-name")
@click.option("-i", "--input-env-file")
@click.pass_context
def run_unit(ctx, unit_name, params=None, output_env_file_name=None, input_env_file=None ):
    click.echo(f"Running unit {unit_name} with input file: {input}")
    
    verify_unit_exist(unit_name)
    verify_if_param_exist_in_unit(params, unit_name, unit_list)
    # default_vars = utils.get_default_vars(ctx)
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)
    # Params is priority. additional vars will be overwritten by params
    params=utils.update_params_with_input_file(additional_vars_from_file,params)
    unit_input_env=get_unit_input_env(unit_name)
        
    role = Role(ctx, None, role_list, get_role_name(unit_name), params, output_env_file_name)
    unit=Unit(unit_name,role,unit_input_env)   
    unit.start()

def verify_unit_exist(unit_name):
    for unit in unit_list:
        if unit_name == unit["name"]:
            return
    print(f"no unit exist with {unit_name}")
    exit(1)

    
def verify_if_param_exist_in_unit(params, unit_name, unit_list):    
    if not params:
        return
    for unit in unit_list:
        if unit_name == unit["name"]:
            unit_config_path = unit["path"] + "/config.yaml"
            with open(unit_config_path, "r") as file:
                unit_config_vars = yaml.safe_load(file)
                roles.verify_if_param_exist_in_role(params, unit_config_vars["unit"]["role"]["name"])    
                
def get_unit_input_env(unit_name):
    for unit in unit_list:
        if unit_name == unit["name"]:
            unit_config_path = unit["path"] + "/config.yaml"
            with open(unit_config_path, "r") as file:
                unit_config_vars = yaml.safe_load(file)
            return unit_config_vars["unit"]["role"]["input_env"]

def get_role_name(unit_name):
    for unit in unit_list:
        if unit_name == unit["name"]:
            print(unit_name)
            return unit["role_name"]
         

def get_config_data(config_file_dir):
    try:
        with open(os.path.join(config_file_dir,"config.yaml"), 'r') as config_file:
            config_data = yaml.safe_load(config_file)
            return config_data
    except FileNotFoundError:
        click.echo(f"Config file '{config_file_dir}/config.yaml' not found.")

def display_unit_info(ctx, unit_name, unit_path, role_name):
    unit_config_data=get_config_data(unit_path)['unit']
    for role in role_list:
        if role_name == role["name"]:
            role_path=role["path"]
    role_config_data=get_config_data(role_path)['role']
    target_main_file=os.path.join(role_path,"main.sh")
    if not os.path.exists(target_main_file):
        target_main_file=os.path.join(role_path,"main.py")
    
    click.echo(f"{Fore.BLUE}Type:{Style.RESET_ALL} Unit")
    click.echo(f"{Fore.BLUE}Name:{Style.RESET_ALL} {unit_name}")
    click.echo(f"{Fore.BLUE}Description:{Style.RESET_ALL} {unit_config_data.get('description','')}")
    click.echo(f"{Fore.BLUE}Example Command:{Style.RESET_ALL}{Fore.RED} loopy units run {unit_name}{Style.RESET_ALL}")
    click.echo(f"{Fore.BLUE}Role:{Style.RESET_ALL}")
    click.echo(f"{Fore.BLUE}  Name:{Style.RESET_ALL} {role_name}")
    click.echo(f"{Fore.BLUE}  Description:{Style.RESET_ALL} {role_config_data.get('description','')}")
    click.echo(f"{Fore.BLUE}  Main File Path:{Style.RESET_ALL} {target_main_file}")
    unit_env_list=unit_config_data['role'].get('input_env',{})
    required_input_keys = Get_required_input_keys(ctx, role_path, role_name)
             
    click.echo(f"{Fore.BLUE}  Input:{Style.RESET_ALL}")    
    no_value_keys=[]
    for required_input_key in required_input_keys:
        if required_input_key in unit_env_list:
            unit_input_env = unit_env_list[required_input_key]
        else:
            no_value_keys.append(required_input_key)
            continue

        if unit_input_env:
            click.echo(f"  - {Fore.GREEN}{required_input_key:<20}:{Style.RESET_ALL} {unit_input_env}")
         
    if len(no_value_keys)> 0:
        for no_value_key in no_value_keys:
            click.echo(f"  - {Fore.GREEN}{no_value_key:<20}:{Style.RESET_ALL} 'no specified'")               
        