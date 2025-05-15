import pytest


@pytest.fixture()
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""

    base_env["SAN_DNS_LIST"] = "minio.minio.svc.cluster.local,minio-minio.test"
    base_env["SAN_IP_LIST"] = "192.168.1.1"
    return base_env
