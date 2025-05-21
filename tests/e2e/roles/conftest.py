# tests/e2e/roles/conftest.py

import os
import subprocess
import pytest
from cli.commands import utils
from pathlib import Path
from core.report_manager import LoopyReportManager
from tests.conftest import generate_random_name
from kubernetes import client, config
import yaml


def ensure_namespace_and_operatorgroup(namespace, operatorgroup_name, operatorgroup_yaml):
    # Load kube config from KUBECONFIG environment variable if available, otherwise use default
    kubeconfig = os.getenv("KUBECONFIG")
    if kubeconfig:
        config.load_kube_config(config_file=kubeconfig)
    else:
        config.load_kube_config()
    v1 = client.CoreV1Api()
    custom_api = client.CustomObjectsApi()

    # Check if namespace exists
    try:
        v1.read_namespace(namespace)
        print(f"Namespace {namespace} already exists")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print(f"Creating namespace {namespace}")
            try:
                v1.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace)))
            except client.exceptions.ApiException as create_e:
                if create_e.status != 409:  # Ignore 409, raise other errors
                    print(f"Namespace {namespace} already exists (409)")
                return
        elif e.status == 409:
            print(f"Namespace {namespace} already exists (409)")
        else:
            raise

    # Check if OperatorGroup exists
    try:
        custom_api.get_namespaced_custom_object(
            group="operators.coreos.com",
            version="v1",
            namespace=namespace,
            plural="operatorgroups",
            name=operatorgroup_name,
        )
        print(f"OperatorGroup {operatorgroup_name} already exists in namespace {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print(f"Creating OperatorGroup {operatorgroup_name} in namespace {namespace}")
            operatorgroup = yaml.safe_load(operatorgroup_yaml)
            try:
                custom_api.create_namespaced_custom_object(
                    group="operators.coreos.com",
                    version="v1",
                    namespace=namespace,
                    plural="operatorgroups",
                    body=operatorgroup,
                )
            except client.exceptions.ApiException as create_e:
                if create_e.status != 409:  # Ignore 409, raise other errors
                    print(f"OperatorGroup {operatorgroup_name} already exists in namespace {namespace} (409)")
        elif e.status == 409:
            print(f"OperatorGroup {operatorgroup_name} already exists in namespace {namespace} (409)")
        else:
            raise


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
    ensure_namespace_and_operatorgroup(namespace, operatorgroup_name, operatorgroup_yaml)


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
