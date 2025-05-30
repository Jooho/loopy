# tests/fvt/roles/test_shell_execute/test_shell_execute.py

import pytest
import subprocess
from pathlib import Path


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_single_command(role_dir, base_env, setup_test_env):
    """Test executing a single command"""
    test_env = {"COMMANDS": "echo 'Hello, World!'", "SHOW_COMMAND": "true"}

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command output file exists
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()

    # Verify command output content
    output_content = output_file.read_text()
    assert "COMMAND: echo 'Hello, World!'" in output_content
    assert "STDOUT:\nHello, World!" in output_content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_multiple_commands(role_dir, base_env, setup_test_env):
    """Test executing multiple commands separated by %%"""
    test_env = {
        "COMMANDS": "echo 'First command' %% echo 'Second command'",
        "SHOW_COMMAND": "true",
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Convert string paths to Path objects before joining
    role_dir_path = Path(base_env["ROLE_DIR"])
    assert (role_dir_path / "0-command.txt").exists()
    assert (role_dir_path / "1-command.txt").exists()

    # Verify command outputs
    with open(role_dir_path / "0-command.txt") as f:
        assert "First command" in f.read()
    with open(role_dir_path / "1-command.txt") as f:
        assert "Second command" in f.read()


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_with_error(role_dir, base_env, setup_test_env):
    """Test executing a command that produces an error"""
    test_env = {"COMMANDS": "nonexistent_command", "SHOW_COMMAND": "true"}

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    # Verify error handling
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()
    content = output_file.read_text()
    assert "STDERR:" in content
    assert "not found" in content.lower()


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_with_comments(role_dir, base_env, setup_test_env):
    """Test executing commands with comments"""
    test_env = {
        "COMMANDS": "echo 'Actual command' %% # This is a comment",
        "SHOW_COMMAND": "true",
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify only the actual command was executed
    output_file = (
        Path(base_env["ROLE_DIR"]) / "0-command.txt"
    )  # Note: index is 1 because first command was a comment
    assert output_file.exists()
    content = output_file.read_text()
    assert "COMMAND: echo 'Actual command'" in content
    assert "STDOUT:\nActual command" in content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_without_show_command(role_dir, base_env, setup_test_env):
    """Test executing commands with SHOW_COMMAND set to false"""
    test_env = {"COMMANDS": "echo 'Hidden command'", "SHOW_COMMAND": "false"}

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command was executed but not shown
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()
    content = output_file.read_text()
    assert "Hidden command" in content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_multi_lines_commands_passing_env(
    role_dir, base_env, setup_test_env
):
    """Test executing multiple commands in a single line"""
    test_env = {
        "COMMANDS": "export test=123 \n echo $test",
        "SHOW_COMMAND": "true",
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command was executed but not shown
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()

    # Verify command output content
    output_content = output_file.read_text()
    assert "COMMAND: export test=123\necho $test" in output_content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_multi_lines_commands_with_for_statement(
    role_dir, base_env, setup_test_env
):
    """Test executing multiple commands in a single line"""
    test_env = {
        "COMMANDS": "for i in 1 2 3; do echo $i; done",
        "SHOW_COMMAND": "true",
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command was executed but not shown
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()

    # Verify command output content
    output_content = output_file.read_text()
    assert "COMMAND: for i in 1 2 3; do echo $i; done" in output_content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_empty_commands(role_dir, base_env, setup_test_env):
    """Test executing when no commands are provided"""
    test_env = {"SHOW_COMMAND": "true"}  # COMMANDS not set

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command output file exists
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()

    # Verify error message is shown
    output_content = output_file.read_text()
    assert "ERROR:No commands provided to execute" in output_content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_special_characters(role_dir, base_env, setup_test_env):
    """Test executing commands with shell-safe special characters (excluding # which is treated as comment)"""
    test_env = {
        "COMMANDS": "echo 'Special chars: $@%^&*()_+-'",
        "SHOW_COMMAND": "true",
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command output file exists
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()

    # Verify command output content
    output_content = output_file.read_text()
    assert "Special chars: $@%^&*()_+-" in output_content


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_shell_execute_mixed_output(role_dir, base_env, setup_test_env):
    """Test executing commands that produce both stdout and stderr output"""
    test_env = {
        "COMMANDS": "echo 'This is stdout' && echo 'This is stderr' >&2",
        "SHOW_COMMAND": "true",
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run(
        ["python3", str(role_dir / "main.py")], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify command output file exists
    output_file = Path(base_env["ROLE_DIR"]) / "0-command.txt"
    assert output_file.exists()

    # Verify both stdout and stderr are captured
    output_content = output_file.read_text()
    assert "STDOUT:\nThis is stdout" in output_content
    assert "STDERR:\nThis is stderr" in output_content
