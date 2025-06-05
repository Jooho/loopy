import pytest
import subprocess
import json
import time
import os


def run_command(cmd, env=None):
    """Helper function to run shell commands"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    return result.stdout, result.stderr, result.returncode


def get_crc_status_json(env=None):
    """Get CRC status in JSON format"""
    stdout, stderr, returncode = run_command("crc status -o json", env)
    if returncode == 0:
        return json.loads(stdout)
    return None


def is_cluster_stopped(env=None):
    """Check if cluster is properly stopped"""
    stdout, stderr, returncode = run_command("crc status", env)
    if returncode != 0:
        return (
            "Machine does not exist" in stdout
            or "crc does not seem to be setup correctly" in stdout
        )

    status = get_crc_status_json(env)
    return status and status.get("openshiftStatus") == "Stopped"


@pytest.mark.openshift_local
@pytest.mark.cluster_lifecycle_tests
class TestOpenShiftLocal:
    @pytest.mark.dependency(name="create_openshift_local_cluster")
    @pytest.mark.order(1)
    def test_openshift_local_installation(self, role_env):
        """Test OpenShift Local installation and cluster startup"""

        # Create a copy of the environment with PATH
        env = os.environ.copy()
        env.update(role_env)

        # Run the role
        result = subprocess.run(
            [
                "./loopy",
                "roles",
                "run",
                "openshift-local-install",
                "-l",
                "-g",
                "-r",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify cluster is running
        status = get_crc_status_json(env)
        assert status is not None, "Failed to get OpenShift Local status"
        assert status.get("openshiftStatus") == "Running", "Cluster is not running"

        # Verify cluster is accessible
        stdout, stderr, returncode = run_command("oc get nodes", env)
        assert returncode == 0, f"Failed to access cluster: {stderr}"

        # Verify console URL is accessible
        stdout, stderr, returncode = run_command("crc console --url", env)
        assert returncode == 0, f"Failed to get console URL: {stderr}"
        assert "https://" in stdout, "Console URL is not in expected format"

    @pytest.mark.dependency(depends=["create_openshift_local_cluster"])
    @pytest.mark.order(2)
    def test_openshift_local_stop(self, role_env):
        """Test stopping OpenShift Local cluster"""
        # Create a copy of the environment with PATH
        env = os.environ.copy()
        env.update(role_env)

        # Run the role
        result = subprocess.run(
            [
                "./loopy",
                "roles",
                "run",
                "openshift-local-uninstall",
                "-l",
                "-g",
                "-r",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify cluster is stopped
        assert is_cluster_stopped(env), "Cluster is not properly stopped"

    @pytest.mark.dependency(depends=["create_openshift_local_cluster"])
    @pytest.mark.order(3)
    def test_openshift_local_delete(self, role_env):
        """Test deleting OpenShift Local cluster"""
        # Create a copy of the environment with PATH
        env = os.environ.copy()
        env["DELETE"] = "0"
        env.update(role_env)

        # Run the role
        result = subprocess.run(
            [
                "./loopy",
                "roles",
                "run",
                "openshift-local-uninstall",
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
        assert is_cluster_stopped(env), "Cluster is not properly stopped"

    @pytest.mark.dependency(depends=["create_openshift_local_cluster"])
    @pytest.mark.order(4)
    def test_openshift_local_cleanup(self, role_env):
        """Test OpenShift Local cleanup"""
        # Create a copy of the environment with PATH
        env = os.environ.copy()
        env["CLEANUP"] = "0"
        env.update(role_env)

        # Run the role
        result = subprocess.run(
            [
                "./loopy",
                "roles",
                "run",
                "openshift-local-uninstall",
                "-l",
                "-g",
                "-r",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify cleanup was successful
        assert is_cluster_stopped(env), "Cluster is not properly stopped"


@pytest.mark.openshift_local
@pytest.mark.cluster_lifecycle_tests
class TestOpenShiftLocalCustom:
    @pytest.mark.dependency(name="create_openshift_local_cluster_custom")
    def test_openshift_local_installation_with_custom_config(self, role_env):
        """Test OpenShift Local installation with custom configuration"""

        # Create a copy of the environment with PATH
        env = os.environ.copy()
        env["MEMORY"] = "16384"
        env["CPU"] = "4"
        env.update(role_env)

        # Run the role
        result = subprocess.run(
            [
                "./loopy",
                "roles",
                "run",
                "openshift-local-install",
                "-l",
                "-g",
                "-r",
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Verify cluster is running
        status = get_crc_status_json(env)
        assert status is not None, "Failed to get OpenShift Local status"
        assert status.get("openshiftStatus") == "Running", "Cluster is not running"

        # Verify cluster is accessible
        stdout, stderr, returncode = run_command("oc get nodes", env)
        assert returncode == 0, f"Failed to access cluster: {stderr}"
