import click
import utils
import yaml
import units
import roles
from component import Role, Unit, Playbook
role_list=utils.initialize("./src/roles", "role")
unit_list=utils.initialize("./src/units", "unit")
playbook_list=utils.initialize("./src/playbooks","playbook")

@click.command(name="list")
def list_playbooks():
    click.echo("Available playbooks:")
    for playbook in playbook_list:
        click.echo(f" - {playbook['name']}")

@click.command(name="show")
@click.argument("playbook_name")
def show_playbook(playbook_name):
    click.echo(f"Details for playbook: {playbook_name}")
    # Add your implementation here

@click.command(name="run")
@click.argument("playbook_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-i", "--input-env-file")
@click.pass_context
def run_playbook(ctx, playbook_name, params,input_env_file=None):
    click.echo(f"Running playbook {playbook_name} with input file: {input}")
    verify_playbook_exist(playbook_name)
    verify_if_param_exist_in_playbook(params, playbook_name, playbook_list)
    default_vars = utils.get_default_vars(ctx)
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)
    # Params is priority. additional vars will be overwritten by params
    params=utils.update_params_with_input_file(additional_vars_from_file,params)        
    
    steps = []
    for playbook in playbook_list:
        if playbook_name == playbook["name"]:
            playbook_config_path = playbook["path"] + "/config.yaml"
            with open(playbook_config_path, "r") as file:
                playbook_config_vars = yaml.safe_load(file)
                steps=playbook_config_vars["playbook"]["steps"]

    playbook = Playbook(playbook_name)
    for index,step in enumerate(steps):
        if list(step)[0] == 'role':
            role_name=step['role']['name']
            additional_input_env=get_role_input_env(step['role'])
            role = Role(ctx, index, default_vars, role_list, role_name, params, None)
            if additional_input_env is not None:
                unit=Unit(role_name+"-unit",role,additional_input_env)
                playbook.add_component(unit)
            else:
                playbook.add_component(role)
        if list(step)[0] == 'unit':            
            unit_name=step['unit']['name']
            unit_input_env=units.get_unit_input_env(unit_name)
            role = Role(ctx, index, default_vars, role_list, units.get_role_name(unit_name), params, None)
            unit=Unit(unit_name,role,unit_input_env)
            
            playbook.add_component(unit)
    playbook.start()

def get_role_input_env(role_info):
    if "input_env" not in role_info:
        return None
    else:
        return role_info["input_env"]
        
                
def verify_playbook_exist(playbook_name):
    for playbook in playbook_list:
        if playbook_name == playbook["name"]:
            return
    print(f"no playbook exist with {playbook_name}")
    exit(1)


def verify_if_param_exist_in_playbook(params, playbook_name, playbook_list):    
    if not params:
        return
    for playbook in playbook_list:
        if playbook_name == playbook["name"]:
            playbook_config_path = playbook["path"] + "/config.yaml"
            with open(playbook_config_path, "r") as file:
                playbook_config_vars = yaml.safe_load(file)
                first_comp_info=playbook_config_vars["playbook"]["steps"][0]
                first_comp_type=list(first_comp_info.keys())[0]
                if first_comp_type == "role":
                  roles.verify_if_param_exist_in_role(params, first_comp_info["role"]["name"], role_list)
                elif first_comp_type == "unit":  
                  units.verify_if_param_exist_in_unit(params,first_comp_info['unit']['name'] , unit_list,role_list)
                           
