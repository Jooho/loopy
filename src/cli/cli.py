import click
from core.context import LoopyContext
from .commands.roles import list_roles, show_role, test_role, run_role
from .commands.units import list_units, show_unit, run_unit
from .commands.playbooks import list_playbooks, show_playbook, run_playbook
from .commands.run import run_command


@click.group()
def roles():
    pass


roles.add_command(list_roles)
roles.add_command(show_role)
roles.add_command(test_role)
roles.add_command(run_role)


@click.group()
def units():
    pass


units.add_command(list_units)
units.add_command(show_unit)
units.add_command(run_unit)


@click.group()
def playbooks():
    pass


playbooks.add_command(list_playbooks)
playbooks.add_command(show_playbook)
playbooks.add_command(run_playbook)


@click.group()
@click.pass_context
def cli(ctx):
    try:
        ctx.obj = LoopyContext(ctx.obj or {})
    except Exception as e:
        click.echo(f"Error initializing Loopy context: {e}", err=True)
        ctx.exit(1)
    pass


cli.add_command(roles)
cli.add_command(units)
cli.add_command(playbooks)
cli.add_command(run_command, name="run")
