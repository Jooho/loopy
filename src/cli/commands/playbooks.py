# fmt: off
import os
import click
import utils
import yaml
import units
import roles
import loopy_report 
from component import Role, Unit, Playbook, Get_default_input_value, Get_required_input_keys
from colorama import Fore, Style, Back

role_list = utils.initialize("./src/roles", "role")
unit_list = utils.initialize("./src/units", "unit")
playbook_list = utils.initialize("./src/playbooks", "playbook")


@click.command(name="list")
def list_playbooks():
    click.echo("Available playbooks:")
    for playbook in sorted(playbook_list, key=lambda x: x["name"]):
        click.echo(f" - {playbook['name']}")


@click.command(name="show")
@click.argument("playbook_name")
@click.option("-v", "--detail-information",is_flag=True)
@click.pass_context
def show_playbook(ctx, playbook_name, detail_information):
    verify_playbook_exist(playbook_name)
    for item in playbook_list:
        if playbook_name == item["name"]:
            playbook_path = item["path"]
    display_playbook_info(ctx, playbook_name, playbook_path, detail_information)


@click.command(name="run")
@click.argument("playbook_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-i", "--input-env-file")
@click.pass_context
def run_playbook(ctx, playbook_name, params, input_env_file=None):
    utils.print_logo()
    click.echo(f"Running playbook {playbook_name}")
    
    verify_playbook_exist(playbook_name)
    verify_if_param_exist_in_playbook(ctx,params, playbook_name, playbook_list)

    additional_vars_from_file = utils.load_env_file_if_exist(input_env_file)

    # Params is priority. additional vars will be overwritten by params
    params = utils.update_params_with_input_file(additional_vars_from_file, params)

    steps = []
    for playbook in playbook_list:
        if playbook_name == playbook["name"]:
            playbook_config_path = playbook["path"] + "/config.yaml"
            with open(playbook_config_path, "r") as file:
                playbook_config_vars = yaml.safe_load(file)
                steps = playbook_config_vars["playbook"]["steps"]

    playbook = Playbook(playbook_name)
    role_count=0
    for py_index, step in enumerate(steps):
        if list(step)[0] == "role":
            role_name = step["role"]["name"]
            additional_input_env = utils.get_input_env_from_config_data(step["role"])
            role = Role(
                ctx, role_count, role_list, role_name, params, None, additional_input_env
            )
            if additional_input_env is not None:
                unit = Unit(role_name + "-unit")
                unit.add_component(role)
                playbook.add_component(unit)
            else:
                playbook.add_component(role)
            role_count+=1
        if list(step)[0] == "unit":
            unit_name = step["unit"]["name"]
            unit_input_env_in_playbook = utils.get_input_env_from_config_data(step["unit"])

            unit = Unit(unit_name)
            unit_config_data = utils.get_config_data_by_name(ctx, unit_name, "unit", unit_list )["unit"]
            # When Unit have multiple roles
            if "steps" in unit_config_data:
                for index, step in enumerate(unit_config_data["steps"]):
                    if list(step)[0] != "role":
                        click.echo("Unit can not include another unit in the steps")
                        exit(1)
                    role_name = step["role"]["name"]
                    additional_input_env = utils.get_input_env_from_config_data( step["role"] )
                    if index == 0:
                        merged_unit_input_env_in_py_with_role_input_env = {**unit_input_env_in_playbook, **additional_input_env} if unit_input_env_in_playbook and additional_input_env else (unit_input_env_in_playbook or additional_input_env or {})
                        role = Role( ctx, role_count, role_list, role_name, params, None, merged_unit_input_env_in_py_with_role_input_env )
                        role_count+=1
                    else:
                        role = Role( ctx,  role_count, role_list, role_name, params, None, additional_input_env )
                        role_count+=1
                    unit.add_component(role)
            # When Unit have single role
            else:
                additional_input_env = utils.get_input_env_from_config_data( unit_config_data["role"] )
                role = Role(   ctx, role_count, role_list, utils.get_first_role_name_in_unit_by_unit_name( unit_name, unit_list ), params, None, additional_input_env )
                unit.add_component(role)

            playbook.add_component(unit)
    playbook.start()
    loopy_report.summary(ctx,"playbook",playbook_config_vars,unit_list)

def merge_unit_input_env_in_py_with_first_role_in_unit(unit_name, playbook_unit_input_env):
    for unit in unit_list:
        if unit_name == unit["name"]:
            unit_config_path = unit["path"] + "/config.yaml"
            with open(unit_config_path, "r") as file:
                unit_config_vars = yaml.safe_load(file)
                unit_input_env = unit_config_vars["unit"]["role"]["input_env"]
                if playbook_unit_input_env is not None:
                    for key, value in playbook_unit_input_env.items():
                        unit_input_env[key] = value
                    return unit_input_env
                return unit_input_env

def verify_playbook_exist(playbook_name):
    for playbook in playbook_list:
        if playbook_name == playbook["name"]:
            return
    print(f"no playbook exist with {playbook_name}")
    exit(1)

def verify_if_param_exist_in_playbook(ctx, params, playbook_name, playbook_list):
    if not params:
        return
    for playbook in playbook_list:
        if playbook_name == playbook["name"]:
            playbook_config_path = playbook["path"] + "/config.yaml"
            with open(playbook_config_path, "r") as file:
                playbook_config_vars = yaml.safe_load(file)
                first_comp_info = playbook_config_vars["playbook"]["steps"][0]
                first_comp_type = list(first_comp_info.keys())[0]
                if first_comp_type == "role":
                    roles.verify_if_param_exist_in_role(ctx, params, first_comp_info["role"]["name"])
                elif first_comp_type == "unit":
                    units.verify_if_param_exist_in_unit( params, first_comp_info["unit"]["name"], unit_list, role_list)

def display_playbook_info(ctx, playbook_name, playbook_path, detail_information):
    playbook_config_data = utils.get_config_data_by_config_file_dir(ctx,playbook_path)["playbook"]
    steps = playbook_config_data["steps"]
    role_path=""
    role_name=""
    unit_path=""
    unit_name=""
    # If the first step is role
    if "role" in steps[0]:
        for role in role_list:
            if steps[0]["role"]["name"] == role["name"]:
                role_path = role["path"]
                role_name = role["name"]
        role_config_data = utils.get_config_data_by_config_file_dir(ctx,role_path)["role"]
    # If the first step is not role    
    else:
        for unit in unit_list:
            if steps[0]["unit"]["name"] == unit["name"]:
                unit_path = unit["path"]
                unit_name = unit["name"]
        # Get the first unit config data        
        unit_config_data = utils.get_config_data_by_config_file_dir(ctx,unit_path)["unit"]
        # Get steps for role in the first unit
        unit_steps=unit_config_data['steps']
        for role in role_list:
            # Get the first role in the unit steps
            if unit_steps[0]["role"]["name"] == role["name"]:
                role_path = role["path"]
                role_name = role["name"]    
        role_config_data = utils.get_config_data_by_config_file_dir(ctx,role_path)["role"]

    required_role_input_keys = Get_required_input_keys(ctx, role_path, role_name)
    target_main_file = os.path.join(role_path, "main.sh")
    if not os.path.exists(target_main_file):
        target_main_file = os.path.join(role_path, "main.py")

    click.echo(f"{Fore.BLUE}Type:{Style.RESET_ALL} Playbook")
    click.echo(f"{Fore.BLUE}Name:{Style.RESET_ALL} {playbook_name}")
    click.echo(f"{Fore.BLUE}Description:{Style.RESET_ALL} {playbook_config_data.get('description','')}")
    click.echo(f"{Fore.BLUE}Playbook Config File:{Style.RESET_ALL} {playbook_path}/config.yaml")
    click.echo(f"{Fore.BLUE}Example Command:{Style.RESET_ALL}{Fore.RED} loopy playbooks run {playbook_name}{Style.RESET_ALL}")
    
    click.echo(f"{Fore.BLUE}Playbook Steps:{Style.RESET_ALL}")
    for step in steps:       
        if "role" in step:
            if 'description' in step['role']:
                click.echo(f"{Fore.LIGHTYELLOW_EX}  -> {step['role']['description']}{Style.RESET_ALL}")
            else:
                click.echo(f"{Fore.LIGHTYELLOW_EX}  -> {step['role']['name']}{Style.RESET_ALL}")
        else:
            if 'description' in step['unit']:
                click.echo(f"{Fore.LIGHTYELLOW_EX}  -> {step['unit']['description']}{Style.RESET_ALL}")
            else:                
                click.echo(f"{Fore.LIGHTYELLOW_EX}  -> {step['unit']['name']}{Style.RESET_ALL}")
            
    if detail_information:
        if "unit" in steps[0]:
            click.echo(f"{Fore.BLUE}First Unit:{Style.RESET_ALL}")
            click.echo(f"{Fore.BLUE}  Name:{Style.RESET_ALL} {unit_name}")
            click.echo(f"{Fore.BLUE}  Description:{Style.RESET_ALL} {unit_config_data.get('description','')}")
            click.echo(f"{Fore.BLUE}  Example Command:{Style.RESET_ALL}{Fore.RED} loopy units run {unit_name}{Style.RESET_ALL}")
            click.echo(f"{Fore.BLUE}    Type:{Style.RESET_ALL} Role")
            click.echo(f"{Fore.BLUE}    Name:{Style.RESET_ALL} {role_name}")
            click.echo(f"{Fore.BLUE}    Description:{Style.RESET_ALL} {role_config_data.get('description','')}")
            click.echo(f"{Fore.BLUE}    Main File Path:{Style.RESET_ALL} {target_main_file}")
        else:
            click.echo(f"{Fore.BLUE}First Role:{Style.RESET_ALL}")
            click.echo(f"{Fore.BLUE}  Name:{Style.RESET_ALL} {role_name}")
            click.echo(f"{Fore.BLUE}  Description:{Style.RESET_ALL} {role_config_data.get('description','')}")
            click.echo(f"{Fore.BLUE}  Main File Path:{Style.RESET_ALL} {target_main_file}")

        if "unit" in steps[0]:
            py_unit_env_list = steps[0]["unit"].get("input_env", {})            
            click.echo(f"{Fore.BLUE}    Input:{Style.RESET_ALL}")

            no_value_keys_in_py = []
            # Process required input keys with input values in playbook unit
            for required_role_input_key in required_role_input_keys:
                if required_role_input_key in py_unit_env_list:
                    unit_input_env = py_unit_env_list[required_role_input_key]
                else:
                    no_value_keys_in_py.append(required_role_input_key)
                    continue

                if unit_input_env:
                    click.echo(f"    - {Fore.GREEN}{required_role_input_key:<20}:{Style.RESET_ALL} {unit_input_env}")
            # Process required input keys without values in unit input values
            final_no_value_keys = []
            if len(no_value_keys_in_py) > 0:
                unit_env_list = unit_config_data['steps'][0]["role"].get("input_env", {})
                for required_role_input_key_without_value in no_value_keys_in_py:
                    if required_role_input_key_without_value in unit_env_list:
                        role_input_env = unit_env_list[required_role_input_key_without_value]
                    else:
                        final_no_value_keys.append(required_role_input_key_without_value)
                        continue

                    if role_input_env:
                        click.echo(f"    - {Fore.GREEN}{required_role_input_key_without_value:<20}:{Style.RESET_ALL} {role_input_env}")

            # Process required input keys without values
            for no_value_key in final_no_value_keys:
                click.echo(f"    - {Fore.GREEN}{no_value_key:<20}:{Style.RESET_ALL} 'no specified'")
        else:
            py_role_input_env_list = steps[0].get("role", {}).get("input_env", {})

            click.echo(f"{Fore.BLUE}  Input:{Style.RESET_ALL}")
            no_value_keys_in_py = []
            # Process required input keys and their values
            for required_role_input_key in required_role_input_keys:
                if required_role_input_key in py_role_input_env_list:
                    role_input_env = py_role_input_env_list[required_role_input_key]
                else:
                    no_value_keys_in_py.append(required_role_input_key)
                    continue
                if role_input_env:
                    click.echo(f"  - {Fore.GREEN}{required_role_input_key:<20}:{Style.RESET_ALL} {role_input_env}")
            
            # Process default input variables and their values
            final_no_value_keys = []
            if len(no_value_keys_in_py) > 0:
                role_env_list = role_config_data.get("input_env", {})
                for required_role_input_key_without_value in no_value_keys_in_py:
                    if required_role_input_key_without_value in role_env_list:
                        input_name = required_role_input_key_without_value.get("name", "")
                        default_input_value = Get_default_input_value(ctx, role_path, role_name, None, input_name)
                        click.echo(f"  - {Fore.GREEN}{input_name:<20}:{Style.RESET_ALL} {default_input_value}")
                    else:
                        final_no_value_keys.append(required_role_input_key_without_value)
                        continue
                            
            for no_value_key in final_no_value_keys:
                click.echo(f"    - {Fore.GREEN}{no_value_key:<20}:{Style.RESET_ALL} 'no specified'")
