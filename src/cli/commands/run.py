import os
import re
import subprocess
from typing import Dict
import logging
import click
from commons.python.py_utils import error, die, info, custom_log

logger = logging.getLogger(__name__)


class RunCommand:
    def __init__(self):
        self.scripts_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "dev", "scripts"
        )

    def list_scripts(self) -> int:
        """
        List all available scripts.

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Collect all available commands
            available_commands = set()
            for filename in os.listdir(self.scripts_dir):
                if filename.endswith((".sh", ".py")):
                    # Remove extension to get command name
                    command_name = os.path.splitext(filename)[0]
                    available_commands.add(command_name)

            # Print available commands
            print("Available commands:")
            for cmd in sorted(available_commands):
                print(f"- {cmd}")
            return 0
        except Exception as e:
            logger.error(f"Error listing scripts: {str(e)}")
            return 1

    def show_script_info(self, command_name: str) -> int:
        """
        Show detailed information about a specific script.

        Args:
            command_name: Name of the command to show info for

        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        try:
            # Find the command file
            script_path = os.path.join(self.scripts_dir, f"{command_name}.sh")
            python_path = os.path.join(self.scripts_dir, f"{command_name}.py")

            # Determine which file to use
            if os.path.exists(script_path):
                self._print_script_info(script_path)
                return 0
            elif os.path.exists(python_path):
                self._print_script_info(python_path)
                return 0
            else:
                user_msg = (
                    f"There is no '{command_name}' command in {self.scripts_dir}."
                )
                die(user_msg)
        except Exception as e:
            logger.error(f"Error showing script info: {str(e)}")
            error(f"Error showing script info: {str(e)}")
            return 1

    def _print_script_info(self, file_path: str):
        """Print script information including description and parameters"""
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Extract description
            description_match = re.search(
                r"#\s*Description:\s*(.*?)(?:\n#|\n\n|\n$)", content, re.DOTALL
            )
            description = (
                description_match.group(1).strip()
                if description_match
                else "No description available"
            )

            # Extract parameters
            params_match = re.search(
                r"#\s*Available Parameters:(.*?)(?:\n\n|\n$)", content, re.DOTALL
            )
            params = (
                params_match.group(1).strip()
                if params_match
                else "No parameters documented"
            )

            custom_log(f"File: {os.path.basename(file_path)}", "green")
            custom_log(f"Description: {description}", "blue")
            custom_log("Available Parameters:", "blue")
            # Format parameters as bullet points
            if params != "No parameters documented":
                param_lines = params.split("\n")
                for line in param_lines:
                    if line.strip():
                        # Remove leading # and spaces, then add bullet point
                        clean_line = line.strip().lstrip("#").strip()
                        custom_log(f"- {clean_line}", "light_sky")
            else:
                custom_log(params, "light_sky")
            print("----------------------------------------")
        except Exception as e:
            logger.error(f"Error reading script {file_path}: {str(e)}")

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
            user_msg = f"There is no '{command_name}' command."
            logger.error(f"Command '{command_name}' not found in {self.scripts_dir}")
            error(user_msg)
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
@click.option("--list", "list_cmd", is_flag=True, help="List all available commands")
@click.option(
    "--info", "info_cmd", is_flag=True, help="Show detailed information about a command"
)
@click.argument("command_name", required=False)
@click.option("-p", multiple=True, help="Parameter in KEY=VALUE format")
@click.option("--clean", is_flag=True, help="Clean up resources before running")
def run(list_cmd, info_cmd, command_name, p, clean):
    """Run a dev command with the given name and parameters"""
    command = RunCommand()

    # Handle list command
    if list_cmd:
        return command.list_scripts()

    # Handle info command
    if info_cmd:
        if not command_name:
            error("Command name is required for --info option")
            return 1
        return command.show_script_info(command_name)

    # Handle direct command execution
    if command_name:
        params = {}
        for param in p:
            if "=" in param:
                key, value = param.split("=", 1)
                params[key] = value
        if clean:
            params["CLEAN"] = "true"
        return command.run(command_name, params)

    # If no command is specified
    error("No command specified. Use --list to see available commands.")
    return 1
