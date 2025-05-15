import pytest
import subprocess
import os
from tests.conftest import timeout


@pytest.mark.e2e
@pytest.mark.e2e_roles
@pytest.mark.cluster_tests
@pytest.mark.order(1)
def test_operator_install_default(role_env):
    """Test the full command line behavior of operator-install role"""
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
            "operator-install",
            "-p",
            f"OPERATOR_NAME={role_env['OPERATOR_NAME']}",
            "-p",
            f"OPERATOR_NAMESPACE={role_env['OPERATOR_NAMESPACE']}",
            "-p",
            f"OPERATOR_LABEL={role_env['OPERATOR_LABEL']}",
            "-p",
            f"SUBSCRIPTION_NAME={role_env['SUBSCRIPTION_NAME']}",
            "-p",
            f"CATALOGSOURCE_NAME={role_env['CATALOGSOURCE_NAME']}",
            "-p",
            f"CATALOGSOURCE_NAMESPACE={role_env['CATALOGSOURCE_NAMESPACE']}",
            "-p",
            f"CHANNEL={role_env['CHANNEL']}",
            "-p",
            f"INSTALL_APPROVAL={role_env['INSTALL_APPROVAL']}",
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
    assert (
        "condition met" in result.stdout
    ), f"'condition met' not found in output: {result.stdout}"


@pytest.mark.e2e
@pytest.mark.e2e_roles
@pytest.mark.cluster_tests
@pytest.mark.order(2)
def test_operator_delete(role_env):
    """Test the full command line behavior of operator-install role"""
    # Create a copy of the environment with PATH
    env = os.environ.copy()
    env.update(role_env)

    # Run the loopy command
    result = subprocess.run(
        [
            "./loopy",
            "roles",
            "run",
            "operator-uninstall",
            "-p",
            f"OPERATOR_NAME={role_env['OPERATOR_NAME']}",
            "-p",
            f"OPERATOR_NAMESPACE={role_env['OPERATOR_NAMESPACE']}",
            "-p",
            f"SUBSCRIPTION_NAME={role_env['SUBSCRIPTION_NAME']}",
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
            "get",
            "pod",
            "-l",
            role_env["OPERATOR_LABEL"],
            "-n",
            role_env["OPERATOR_NAMESPACE"],
            "--ignore-not-found",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Operator pod not ready: {result.stderr}"
    assert result.stderr == "", f"Operator pod found: {result.stderr}"

    result = subprocess.run(
        "oc get csv --no-headers | grep minio | wc -l",
        shell=True,
        capture_output=True,
        text=True,
    )
    assert (
        result.stdout.strip() == "0"
    ), f"CRD tenants.minio.min.io found: {result.stderr}"
