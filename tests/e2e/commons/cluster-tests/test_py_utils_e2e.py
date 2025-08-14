import pytest
import subprocess
import time
import uuid
from commons.python.py_utils import (
    check_pod_status,
    wait_pod_containers_ready,
    wait_for_pods_ready,
    wait_for_pod_name_ready,
    wait_for_just_created_pod_ready,
    wait_for_csv_installed,
    oc_wait_object_availability,
    oc_wait_return_true,
    check_oc_status,
    check_rosa_access,
    retry,
)


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_check_pod_status():
    """Test checking pod status with actual cluster"""
    # Create a test pod with unique name
    pod_name = f"test-pod-status-{uuid.uuid4().hex[:8]}"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
            "-n",
            namespace,
            "--image=registry.access.redhat.com/rhel7/rhel-tools",
            "--",
            "tail",
            "-f",
            "/dev/null",
        ],
        check=True,
    )

    try:
        # Wait for pod to be ready
        assert wait_for_pod_name_ready(pod_name, namespace) == 0

        # Check pod status
        assert check_pod_status(f"run={pod_name}", namespace) is True

    finally:
        # Cleanup
        subprocess.run(
            ["kubectl", "delete", "pod", pod_name, "-n", namespace, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_wait_pod_containers_ready():
    """Test waiting for pod containers to be ready with actual cluster"""
    # Create a test pod with unique name
    pod_name = f"test-pod-containers-{uuid.uuid4().hex[:8]}"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
            "-n",
            namespace,
            "--image=registry.access.redhat.com/rhel7/rhel-tools",
            "--",
            "tail",
            "-f",
            "/dev/null",
        ],
        check=True,
    )

    try:
        # Wait for containers to be ready
        wait_pod_containers_ready(f"run={pod_name}", namespace)

    finally:
        # Cleanup
        subprocess.run(
            ["kubectl", "delete", "pod", pod_name, "-n", namespace, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_wait_for_pods_ready():
    """Test waiting for pods to be ready with actual cluster"""
    # Create test pods with unique name
    pod_name = f"test-pod-ready-{uuid.uuid4().hex[:8]}"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
            "-n",
            namespace,
            "--image=registry.access.redhat.com/rhel7/rhel-tools",
            "--",
            "tail",
            "-f",
            "/dev/null",
        ],
        check=True,
    )

    try:
        # Wait for pods to be ready
        assert wait_for_pods_ready(f"run={pod_name}", namespace) is True

    finally:
        # Cleanup
        subprocess.run(
            ["kubectl", "delete", "pod", pod_name, "-n", namespace, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_wait_for_pod_name_ready():
    """Test waiting for specific pod to be ready with actual cluster"""
    # Create a test pod with unique name
    pod_name = f"test-pod-name-{uuid.uuid4().hex[:8]}"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
            "-n",
            namespace,
            "--image=registry.access.redhat.com/rhel7/rhel-tools",
            "--",
            "tail",
            "-f",
            "/dev/null",
        ],
        check=True,
    )

    try:
        # Wait for pod to be ready
        assert wait_for_pod_name_ready(pod_name, namespace) == 0

    finally:
        # Cleanup
        subprocess.run(
            ["kubectl", "delete", "pod", pod_name, "-n", namespace, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_check_oc_status():
    """Test checking OpenShift connection and user role with actual cluster"""
    check_oc_status()


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_oc_wait_object_availability():
    """Test waiting for object availability with actual cluster"""
    # Create a test pod with unique name
    pod_name = f"test-pod-wait-{uuid.uuid4().hex[:8]}"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
            "-n",
            namespace,
            "--image=registry.access.redhat.com/rhel7/rhel-tools",
            "--",
            "tail",
            "-f",
            "/dev/null",
        ],
        check=True,
    )

    try:
        # Wait for pod to be available
        oc_wait_object_availability(f"kubectl get pod {pod_name} -n {namespace}", 1, 1)

    finally:
        # Cleanup
        subprocess.run(
            ["kubectl", "delete", "pod", pod_name, "-n", namespace, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_retry_with_basic_commands():
    """Test retry function with basic shell commands"""
    # Test with a command that should succeed
    assert retry(3, 1, "echo 'test'", "Testing echo command") is True

    # Test with a command that should fail
    assert retry(3, 1, "false", "Testing false command") is False

    # Test with a command that should fail (non-existent command)
    assert (
        retry(3, 1, "nonexistent_command_123", "Testing non-existent command") is False
    )

    # Test with a command that should succeed after file creation
    test_file = "/tmp/test_retry_file"
    try:
        # Create a file
        subprocess.run(f"touch {test_file}", shell=True, check=True)

        # Test retry with file existence check
        assert retry(3, 1, f"test -f {test_file}", "Testing file existence") is True

    finally:
        # Cleanup
        subprocess.run(f"rm -f {test_file}", shell=True, check=True)


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_retry_with_oc():
    """Test retry function with actual oc commands"""
    try:
        # First verify we can connect to the cluster
        subprocess.run("oc get nodes", shell=True, check=True, capture_output=True)

        # Test with a command that should succeed
        assert retry(10, 3, "oc get nodes", "Waiting for nodes to be available") is True

        # Test with a command that should fail (non-existent namespace)
        assert (
            retry(
                3,
                1,
                "oc get project nonexistent-namespace",
                "Waiting for non-existent project",
            )
            is False
        )

        # Test with a command that should succeed after pod creation
        pod_name = f"test-pod-retry-oc-{uuid.uuid4().hex[:8]}"
        namespace = "default"

        try:
            # Create a pod
            subprocess.run(
                [
                    "oc",
                    "run",
                    pod_name,
                    "-n",
                    namespace,
                    "--image=registry.access.redhat.com/rhel7/rhel-tools",
                    "--",
                    "tail",
                    "-f",
                    "/dev/null",
                ],
                check=True,
                capture_output=True,
            )

            # Wait for pod to be created and ready
            time.sleep(10)

            # Test retry with pod existence check
            assert (
                retry(
                    10,
                    3,
                    f"oc get pod {pod_name} -n {namespace}",
                    "Waiting for pod to exist",
                )
                is True
            )

        finally:
            # Cleanup
            subprocess.run(
                ["oc", "delete", "pod", pod_name, "-n", namespace, "--force", "--grace-period=0"],
                check=True,
                capture_output=True,
            )
    except subprocess.CalledProcessError as e:
        pytest.fail(
            f"Cluster command failed: {e.stderr.decode() if e.stderr else str(e)}"
        )
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")
