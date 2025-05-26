import pytest
import subprocess
import os
import time


@pytest.mark.e2e
@pytest.mark.e2e_dev
@pytest.mark.cluster_tests
def test_debug_pod_basic():
    """Test basic debug-pod command without istio"""
    env = os.environ.copy()
    # # This is for debugging purposes in subprocesses
    # env["LOOPY_DEBUG"] = "1"

    # Run the command
    result = subprocess.run(
        ["./loopy", "run", "debug-pod", "-p", "NAME=debug-pod-basic"],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check if command was successful
    assert result.returncode == 0

    # Verify pod was created
    pod_check = subprocess.run(
        ["kubectl", "get", "pod", "debug-pod-basic"], capture_output=True, text=True
    )
    assert pod_check.returncode == 0

    # Cleanup
    subprocess.run(
        ["kubectl", "delete", "pod", "debug-pod-basic", "--force", "--grace-period=0"]
    )


@pytest.mark.e2e
@pytest.mark.e2e_dev
@pytest.mark.cluster_tests
def test_debug_pod_with_istio():
    """Test debug-pod command with istio sidecar"""
    env = os.environ.copy()
    # # This is for debugging purposes in subprocesses
    # env["LOOPY_DEBUG"] = "1"

    # Run the command with istio
    result = subprocess.run(
        [
            "./loopy",
            "run",
            "debug-pod",
            "-p",
            "WITH_ISTIO=true",
            "-p",
            "NAME=debug-pod-istio",
        ],
        capture_output=True,
        text=True,
        env=env,
    )

    # Check if command was successful
    assert result.returncode == 0

    # Wait for pod to be ready
    time.sleep(5)

    # Verify pod was created with istio sidecar
    pod_check = subprocess.run(
        [
            "kubectl",
            "get",
            "pod",
            "debug-pod-istio",
            "-o",
            "jsonpath='{.metadata.annotations}'",
        ],
        capture_output=True,
        text=True,
    )
    assert pod_check.returncode == 0
    assert "sidecar.istio.io/inject" in pod_check.stdout

    # Cleanup
    subprocess.run(
        ["kubectl", "delete", "pod", "debug-pod-istio", "--force", "--grace-period=0"]
    )
