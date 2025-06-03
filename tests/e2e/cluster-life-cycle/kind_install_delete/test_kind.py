"""End-to-end test cases for kind cluster lifecycle management."""

import os
import subprocess
import pytest


@pytest.mark.cluster_life_cycle_tests
@pytest.mark.dependency(name="create_kind_cluster")
def test_kind_cluster_creation(role_env):
    """Test kind cluster creation with ingress enabled."""
    # Create a copy of the environment with PATH
    env = os.environ.copy()
    env.update(role_env)

    # Run the role
    result = subprocess.run(
        [
            "./loopy",
            "roles",
            "run",
            "kind-install",
            "-l",
            "-g",
            "-r",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify cluster exists
    clusters = subprocess.check_output(["kind", "get", "clusters"]).decode().strip()
    assert f"{role_env['KIND_CLUSTER_NAME']}" in clusters, "Cluster was not created"

    # Verify ingress controller if enabled
    if role_env["ENABLE_INGRESS"] == "0":
        pods = subprocess.check_output(
            [
                "kubectl",
                "get",
                "pods",
                "-n",
                "ingress-nginx",
                "-l",
                "app.kubernetes.io/component=controller",
            ]
        ).decode()
        assert "Running" in pods, "Ingress controller is not running"

    # Verify OLM if enabled
    if role_env["ENABLE_OLM"] == "0":
        pods = subprocess.check_output(["kubectl", "get", "pods", "-n", "olm", "-l", "app=olm-operator"]).decode()
        assert "Running" in pods, "OLM operator is not running"


@pytest.mark.cluster_life_cycle_tests
@pytest.mark.dependency(depends=["create_kind_cluster"])
def test_kind_cluster_deletion(role_env):
    """Test kind cluster deletion."""
    # Create a copy of the environment with PATH
    env = os.environ.copy()
    env.update(role_env)

    # Run the uninstall role
    result = subprocess.run(
        [
            "./loopy",
            "roles",
            "run",
            "kind-uninstall",
            "-l",
            "-g",
            "-r",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify cluster is deleted
    clusters = subprocess.check_output(["kind", "get", "clusters"]).decode().strip()
    assert f"{role_env['KIND_CLUSTER_NAME']}" not in clusters, "Cluster was not deleted"
