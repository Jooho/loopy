import pytest

# from pathlib import Path
# from tests.conftest import generate_random_name

# @pytest.fixture(scope="class")
# def role_dir():
#     """Fixture providing the path to the role directory"""
#     return Path("default_provided_services/roles")

# @pytest.fixture(scope="class")
# def output_dir(tmp_path_factory,generate_random_name):
#     """Fixture providing a temporary directory for test outputs"""
#     return tmp_path_factory.mktemp("/tmp/ms_cli/"+generate_random_name())


@pytest.fixture(scope="class")
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""

    base_env["SAN_DNS_LIST"] = "minio.minio.svc.cluster.local,minio-minio.test"
    base_env["SAN_IP_LIST"] = "192.168.1.1"
    return base_env
