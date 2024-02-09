import click
import utils
import os
import yaml
from component import Role, Playbook

role_list = utils.initialize("./src/roles","role")

@click.command(name="list")
def list_roles():
    click.echo("Available roles:")
    for item in role_list:
        click.echo(f" - {item['name']}")


@click.command(name="show")
@click.argument("role_name")
def show_role(role_name):
    click.echo(f"Details for role: {role_name}")
    # Add your implementation here


@click.command(name="test")
@click.argument("role_name")
def test_role(role_name):
    click.echo(f"Running tests for role: {role_name}")
    # Add your implementation here


@click.command(name="run")
@click.argument("role_name")
@click.option("-p", "--params", multiple=True, callback=utils.parse_key_value_pairs)
@click.option("-o", "--output-env-file-name")
@click.option("-i", "--input-env-file")
@click.pass_context
def run_role(ctx, role_name, params=None, output_env_file_name=None, input_env_file=None):
    # role command specific validation
    verify_role_exist(role_name)
    verify_if_param_exist_in_role(params, role_name)
    default_vars = utils.get_default_vars(ctx)
    additional_vars_from_file=utils.load_env_file_if_exist(input_env_file)
    # Params is priority. additional vars will be overwritten by params
    params=utils.update_params_with_input_file(additional_vars_from_file,params)    

    role = Role(ctx, None, default_vars, role_list, role_name, params, output_env_file_name)
    role.start()


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
        print(f"no input enviroment name exist: {target_param}")
        exit(1)
