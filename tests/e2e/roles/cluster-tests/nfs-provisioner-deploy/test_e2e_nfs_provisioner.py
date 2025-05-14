import pytest
import subprocess
import os
from tests.conftest import timeout
from pathlib import Path

@pytest.mark.e2e
@pytest.mark.e2e_roles
@pytest.mark.cluster_tests
def test_nfs_provisioner_default(role_env):
    """Test the full command line behavior of nfs-provisioner role"""
    # Create a copy of the environment with PATH
    env = os.environ.copy()
    # This is for debugging purposes in subprocesses
    # env["LOOPY_DEBUG"] = "1"
    env.update(role_env)

    # Run the loopy command
    result = subprocess.run(
        [
            "./loopy",
            "roles",
            "run",
            "nfs-provisioner-deploy",
            "-p",
            f"NFS_PROVISIONER_NS={role_env['NFS_PROVISIONER_NS']}",
            "-p",
            f"NFS_PROVISIONER_NAME={role_env['NFS_PROVISIONER_NAME']}",
            "-p",
            f"PVC_STORAGECLASS_NAME={role_env['PVC_STORAGECLASS_NAME']}",
            "-p",
            f"NFS_STORAGECLASS_NAME={role_env['NFS_STORAGECLASS_NAME']}",
            "-p",
            f"STORAGE_SIZE={role_env['STORAGE_SIZE']}",
            "-p",
            f"CATALOGSOURCE_NAME={role_env['CATALOGSOURCE_NAME']}",
            "-p",
            f"CATALOGSOURCE_NAMESPACE={role_env['CATALOGSOURCE_NAMESPACE']}",            
            "-l",
            "-g",
            "-r",
        ],
        capture_output=True,
        text=True,
        env=env,  # Add environment variables
    )

    # Verify command execution
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    result = subprocess.run(
        [
            "oc",
            "wait",
            "--for=condition=Ready",
            "pod",
            "-l",
            role_env["OPERATOR_LABEL"],
            "-n",
            role_env["OPERATOR_NAMESPACE"],
            f"--timeout={timeout}s",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Operator pod not ready: {result.stderr}"
    assert "condition met" in result.stdout, f"'condition met' not found in output: {result.stdout}"


    result = subprocess.run(
        [
            "oc",
            "wait",
            "--for=condition=Ready",
            "pod",
            "-l",
            role_env["NFS_SERVER_LABEL"],
            "-n",
            role_env["NFS_PROVISIONER_NS"],
            f"--timeout={timeout}s",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Operator pod not ready: {result.stderr}"
    assert "condition met" in result.stdout, f"'condition met' not found in output: {result.stdout}"

