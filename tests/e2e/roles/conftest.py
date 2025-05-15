# tests/e2e/roles/conftest.py

import os
import subprocess
import pytest
from cli.commands import utils
from pathlib import Path
from core.report_manager import LoopyReportManager
from tests.conftest import generate_random_name


def ensure_namespace_and_operatorgroup(
    namespace, operatorgroup_name, operatorgroup_yaml
):
    # Ensure namespace exists
    ns_check = subprocess.run(
        ["oc", "get", "namespace", namespace], capture_output=True, text=True
    )
    if ns_check.returncode != 0:
        subprocess.run(["oc", "create", "namespace", namespace], check=True)

    # Ensure OperatorGroup exists
    og_check = subprocess.run(
        ["oc", "get", "operatorgroup", operatorgroup_name, "-n", namespace],
        capture_output=True,
        text=True,
    )
    if og_check.returncode != 0:
        subprocess.run(
            ["oc", "apply", "-f", "-"], input=operatorgroup_yaml, text=True, check=True
        )


@pytest.fixture(scope="session", autouse=True)
def setup_operator_namespace_and_group():
    namespace = "openshift-operators"
    operatorgroup_name = "global-operator-group"
    operatorgroup_yaml = """
apiVersion: operators.coreos.com/v1
kind: OperatorGroup
metadata:
  name: global-operator-group
  namespace: openshift-operators
spec: {}
"""
    ensure_namespace_and_operatorgroup(
        namespace, operatorgroup_name, operatorgroup_yaml
    )


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
        "OUTPUT_TARGET_DIR": generate_random_name(),
    }


@pytest.fixture(scope="function", autouse=True)
def cleanup_output_dir(base_env):
    yield

    output_root_dir = Path(base_env["OUTPUT_ROOT_DIR"]) / base_env["OUTPUT_TARGET_DIR"]
    if output_root_dir and os.path.exists(output_root_dir):
        try:
            utils.safe_rmtree(output_root_dir)
        except RuntimeError as e:
            pytest.fail(f"Error deleting folder: {e}", pytrace=True)
