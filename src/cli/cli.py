import click

from .commands.roles import list_roles, show_role, test_role, run_role
from .commands.units import list_units, show_unit, run_unit
from .commands.playbooks import list_playbooks, show_playbook, run_playbook

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
def cli():
    pass

cli.add_command(roles)
cli.add_command(units)
cli.add_command(playbooks)


