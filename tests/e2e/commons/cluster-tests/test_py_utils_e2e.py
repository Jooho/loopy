import pytest
import subprocess
import time
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
)


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_check_pod_status():
    """Test checking pod status with actual cluster"""
    # Create a test pod
    pod_name = "test-pod-status"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
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
            ["kubectl", "delete", "pod", pod_name, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_wait_pod_containers_ready():
    """Test waiting for pod containers to be ready with actual cluster"""
    # Create a test pod
    pod_name = "test-pod-containers"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
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
            ["kubectl", "delete", "pod", pod_name, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_wait_for_pods_ready():
    """Test waiting for pods to be ready with actual cluster"""
    # Create test pods
    pod_name = "test-pod-ready"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
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
            ["kubectl", "delete", "pod", pod_name, "--force", "--grace-period=0"],
            check=True,
        )


@pytest.mark.e2e
@pytest.mark.cluster_tests
@pytest.mark.common
def test_wait_for_pod_name_ready():
    """Test waiting for specific pod to be ready with actual cluster"""
    # Create a test pod
    pod_name = "test-pod-name"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
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
            ["kubectl", "delete", "pod", pod_name, "--force", "--grace-period=0"],
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
    # Create a test pod
    pod_name = "test-pod-wait"
    namespace = "default"
    subprocess.run(
        [
            "kubectl",
            "run",
            pod_name,
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
            ["kubectl", "delete", "pod", pod_name, "--force", "--grace-period=0"],
            check=True,
        )
