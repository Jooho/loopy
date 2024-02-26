import click
import utils
import yaml
import roles
from component import Role, Unit, Playbook
unit_list=utils.initialize("./src/units", "unit")
role_list=utils.initialize("./src/roles", "role")

@click.command(name="list")
def list_units():
    click.echo("Available units:")
    for unit in unit_list:
        click.echo(f" - {unit['name']}")

@click.command(name="show")
@click.argument("unit_name")
def show_unit(unit_name):
    click.echo(f"Details for unit: {unit_name}")
    # Add your implementation here


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
    default_vars = utils.get_default_vars(ctx)
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)
    # Params is priority. additional vars will be overwritten by params
    params=utils.update_params_with_input_file(additional_vars_from_file,params)
    unit_input_env=get_unit_input_env(unit_name)
        
    role = Role(ctx, None, default_vars, role_list, get_role_name(unit_name), params, output_env_file_name)
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
            return unit["role_name"]
        
    
