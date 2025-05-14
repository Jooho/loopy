import pytest


@pytest.fixture()
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""

    base_env["OPERATOR_NAME"] = "minio-operator"
    base_env["OPERATOR_NAMESPACE"] = "openshift-operators"
    base_env["OPERATOR_LABEL"] = "name=minio-operator"
    base_env["SUBSCRIPTION_NAME"] = "minio-operator"
    base_env["CATALOGSOURCE_NAME"] = "operatorhubio-catalog"
    base_env["CATALOGSOURCE_NAMESPACE"] = "olm"
    base_env["CHANNEL"] = "stable"
    base_env["INSTALL_APPROVAL"] = "Automatic"
    return base_env
