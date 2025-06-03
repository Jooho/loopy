import os
import pytest
import yaml
from pathlib import Path
import subprocess
import uuid


@pytest.fixture(scope="session")
def base_env():
    """Fixture providing base environment variables needed for all tests"""
    return {
        "SHOW_DEBUG_LOG": "false",
        "STOP_WHEN_FAILED": "false",
        "STOP_WHEN_ERROR_HAPPENED": "false",
        "ENABLE_LOOPY_LOG": "false",
        "USE_KIND": "true",
        "CLUSTER_API_URL": "",
        "CLUSTER_ADMIN_ID": "",
        "CLUSTER_ADMIN_PW": "",
        "OUTPUT_ROOT_DIR": "/tmp/e2e_loopy_result",
        "OUTPUT_TARGET_DIR": str(uuid.uuid4()),
    }


@pytest.fixture()
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""
    base_env["KIND_CLUSTER_NAME"] = "kind"
    base_env["ENABLE_INGRESS"] = "0"  # 0 means true in the role
    base_env["ENABLE_OLM"] = "0"  # 1 means false in the role
    base_env["NGINX_INGRESS_VERSION"] = "1.10.1"
    base_env["OLM_VERSION"] = "v0.26.0"
    return base_env


@pytest.fixture(scope="session", autouse=True)
def cleanup(base_env):
    yield
    # List of cleanup commands to execute
    cleanup_commands = [
        f"kind delete cluster --name {base_env['KIND_CLUSTER_NAME']}",
    ]

    # Execute each command and check its result
    for cmd in cleanup_commands:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"Warning: Cleanup command failed: {cmd}")
            print(f"Error output: {result.stderr}")
        else:
            print(f"Successfully executed: {cmd}")

    # Clean up output directory
    output_root_dir = Path(base_env["OUTPUT_ROOT_DIR"]) / base_env["OUTPUT_TARGET_DIR"]
    if output_root_dir.exists():
        try:
            import shutil

            shutil.rmtree(output_root_dir)
        except Exception as e:
            print(f"Warning: Failed to clean up output directory: {e}")
