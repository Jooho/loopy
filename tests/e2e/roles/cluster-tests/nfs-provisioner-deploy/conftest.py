import pytest
import subprocess
import sys


@pytest.fixture()
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""

    base_env["NFS_PROVISIONER_NS"] = "nfs-provisioner"
    base_env["NFS_PROVISIONER_NAME"] = "nfs-provisioner-loopy"
    base_env["PVC_STORAGECLASS_NAME"] = "standard"
    base_env["NFS_STORAGECLASS_NAME"] = "nfs"
    base_env["STORAGE_SIZE"] = "100Gi"
    base_env["CATALOGSOURCE_NAME"] = "operatorhubio-catalog"
    base_env["CATALOGSOURCE_NAMESPACE"] = "olm"
    # This is for testing purposes
    base_env["OPERATOR_NAMESPACE"] = "openshift-operators"
    base_env["OPERATOR_LABEL"] = "control-plane=controller-manager"
    base_env["NFS_SERVER_LABEL"] = "app=nfs-provisioner"
    base_env["SUBSCRIPTION_NAME"] = "nfs-provisioner-operator"
    return base_env


@pytest.fixture(scope="function", autouse=True)
def cleanup(base_env):
    yield
    # List of cleanup commands to execute
    cleanup_commands = [
        f"oc delete nfsprovisioner -n {base_env['NFS_PROVISIONER_NS']} {base_env['NFS_PROVISIONER_NAME']} --force",
        f"oc delete subscription {base_env['SUBSCRIPTION_NAME']} -n {base_env['OPERATOR_NAMESPACE']} --force",
        "oc delete csv -n {base_env['OPERATOR_NAMESPACE']} $(oc get csv --no-headers | grep nfs-provisioner-operator | awk '{print $1}') --force",
        f"oc delete deploy nfs-provisioner-operator-controller-manager -n {base_env['OPERATOR_NAMESPACE']} --force",
        "oc delete sc nfs",
        f"oc delete ns {base_env['NFS_PROVISIONER_NS']}",
    ]

    # Execute each command and check its result
    for cmd in cleanup_commands:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode != 0:
            print(f"Warning: Cleanup command failed: {cmd}")
            print(f"Error output: {result.stderr}")
        else:
            print(f"Successfully executed: {cmd}")
