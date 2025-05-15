import pytest
import subprocess
import sys


@pytest.fixture()
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""
    # This is for testing purposes
    base_env["MINIO_LABEL"] = "app=minio"
    base_env["MINIO_NAMESPACE"] = "minio"
    return base_env


@pytest.fixture(scope="function", autouse=True)
def cleanup(base_env):
    yield
    # List of cleanup commands to execute
    cleanup_commands = [
        f"oc delete ns {base_env['MINIO_NAMESPACE']}",
    ]

    # Execute each command and check its result
    for cmd in cleanup_commands:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"Warning: Cleanup command failed: {cmd}")
            print(f"Error output: {result.stderr}")
        else:
            print(f"Successfully executed: {cmd}")
