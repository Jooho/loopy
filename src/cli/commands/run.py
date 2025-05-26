import os
import re
import subprocess
from typing import Dict, Optional
import logging
import click

logger = logging.getLogger(__name__)


class RunCommand:
    def __init__(self):
        self.scripts_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "dev", "scripts"
        )

    def run(self, command_name: str, params: Dict[str, str]) -> int:
        """
        Run a dev command with the given name and parameters.

        Args:
            command_name: Name of the command to run
            params: Dictionary of parameters to pass to the command

        Returns:
            int: Exit code of the command
        """
        # Find the command file
        script_path = os.path.join(self.scripts_dir, f"{command_name}.sh")
        python_path = os.path.join(self.scripts_dir, f"{command_name}.py")

        # Check if TYPE=python is specified
        use_python = params.get("TYPE", "").lower() == "python"

        # Determine which file to use
        if use_python and os.path.exists(python_path):
            return self._run_python_command(python_path, params)
        elif os.path.exists(script_path):
            return self._run_script_command(script_path, params)
        elif os.path.exists(python_path):
            return self._run_python_command(python_path, params)
        else:
            logger.error(f"Command '{command_name}' not found in {self.scripts_dir}")
            return 1

    def _run_script_command(self, script_path: str, params: Dict[str, str]) -> int:
        """Run a shell script command"""
        try:
            # Set environment variables from params
            env = os.environ.copy()
            env.update(params)
            env["LOOPY_DEV_PARAMS"] = " ".join(f"{k}={v}" for k, v in params.items())
            # Make script executable
            os.chmod(script_path, 0o755)

            # Run the script
            result = subprocess.run(script_path, env=env, shell=True)
            return result.returncode

        except Exception as e:
            logger.error(f"Error running script {script_path}: {str(e)}")
            return 1

    def _run_python_command(self, python_path: str, params: Dict[str, str]) -> int:
        """Run a Python command"""
        try:
            # Set environment variables from params
            env = os.environ.copy()
            env.update(params)

            # Run the Python script
            result = subprocess.run(["python", python_path], env=env)
            return result.returncode

        except Exception as e:
            logger.error(f"Error running Python script {python_path}: {str(e)}")
            return 1


@click.command()
@click.argument("command_name")
@click.option("-p", multiple=True, help="Parameter in KEY=VALUE format")
@click.option("--clean", is_flag=True, help="Clean up resources before running")
def run_command(command_name, p, clean):
    """Run a dev command with the given name and parameters"""
    command = RunCommand()
    params = {}
    for param in p:
        if "=" in param:
            key, value = param.split("=", 1)
            params[key] = value
    if clean:
        params["CLEAN"] = "true"
    return command.run(command_name, params)
