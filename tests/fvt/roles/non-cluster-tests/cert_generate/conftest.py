import os
import pytest
from pathlib import Path


@pytest.fixture(scope="class")
def role_name():
    """Fixture providing the path to the shell/execute role directory"""
    return "cert-generate"


@pytest.fixture(scope="class")
def role_dir():
    """Fixture providing the path to the cert/generate role directory"""
    return Path("default_provided_services/roles/cert/generate")


@pytest.fixture(scope="class")
def role_env(base_env):
    """Fixture providing base environment variables needed for all tests"""
    base_env["ROOT_CA_CERT_NAME"] = "root.crt"
    base_env["ROOT_CA_KEY_NAME"] = "root.key"
    base_env["CERT_NAME"] = "test.crt"
    base_env["KEY_NAME"] = "test.key"
    base_env["CSR_NAME"] = "test.csr"
    base_env["CN"] = "test"
    return base_env

