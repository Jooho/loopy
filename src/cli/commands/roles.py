# fmt: off
import os
import click
import utils
import yaml
from component import Role, Get_default_input_value, Get_required_input_keys
from colorama import Fore, Style, Back

role_list = utils.initialize("./src/roles","role")

@click.command(name="list")
def list_roles():
    click.echo("Available roles:")
    for item in sorted(role_list, key=lambda x: x["name"]):
        click.echo(f" - {item['name']}")


@click.command(name="show")
@click.argument("role_name")
@click.pass_context
def show_role(ctx, role_name):
    verify_role_exist(role_name)
  
    for item in role_list:
        if role_name == item["name"]:
            role_path=item["path"]
    display_role_info(ctx, role_name,role_path)
    

@click.command(name="test")
@click.argument("role_name")
def test_role(role_name):
    click.echo(f"Running tests for role: {role_name}")
    click.echo(f"THIS COMMAND is not implemented")
    # Add your implementation here


@click.command(name="run")
@click.argument("role_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-o", "--output-env-file-name")
@click.option("-i", "--input-env-file")
@click.pass_context
def run_role(ctx, role_name, params=None, output_env_file_name=None, input_env_file=None):
    utils.print_logo()
    # role command specific validation
    verify_role_exist(role_name)
    verify_if_param_exist_in_role(params, role_name)
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)
    
    # Params is priority. additional vars will be overwritten by params
    params=utils.update_params_with_input_file(additional_vars_from_file,params)    

    role = Role(ctx, None, role_list, role_name, params, output_env_file_name,None)
    role.start()
    utils.summary(ctx, "role", None,None)

def verify_role_exist(role_name):
    for item in role_list:
        if role_name == item["name"]:
            return
    print(f"no role exist with {role_name}")
    exit(1)


def verify_if_param_exist_in_role(params, role_name):
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
    if input_exist:
        return
    else:
        print(f"{Fore.RED}no input enviroment name exist:{Back.BLUE} {target_param} {Style.RESET_ALL}")
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
