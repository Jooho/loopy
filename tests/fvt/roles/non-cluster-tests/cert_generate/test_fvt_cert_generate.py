import pytest
import subprocess
from pathlib import Path


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_default_cert_generation(role_dir, role_env, setup_test_env):
    """Test Case 1: Default certificate generation (creates new CA and cert)"""
    test_env = {"SAN_DNS_LIST": "minio.minio.svc.cluster.local,minio-minio.test", "SAN_IP_LIST": "192.168.1.1"}

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run([str(role_dir / "main.sh")], env=env, capture_output=True, text=True)

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify all required files are generated
    role_dir_path = Path(role_env["ROLE_DIR"])
    assert role_dir_path.joinpath(role_env["ROOT_CA_CERT_NAME"]).exists()
    assert role_dir_path.joinpath(role_env["ROOT_CA_KEY_NAME"]).exists()
    assert role_dir_path.joinpath(role_env["CERT_NAME"]).exists()
    assert role_dir_path.joinpath(role_env["KEY_NAME"]).exists()

    # Verify certificate content
    cert_path = role_dir_path / role_env["CERT_NAME"]
    verify_result = subprocess.run(
        ["openssl", "verify", "-CAfile", str(role_dir_path / role_env["ROOT_CA_CERT_NAME"]), str(cert_path)],
        capture_output=True,
        text=True,
    )
    assert verify_result.returncode == 0
    assert "OK" in verify_result.stdout


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_cert_generation_with_existing_ca(role_dir, role_env, setup_test_env, tmp_path):
    """Test Case 2: Certificate generation using existing CA"""
    # First create a CA
    ca_dir = tmp_path / "ca"
    ca_dir.mkdir()

    # Generate CA certificate and key
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-sha256",
            "-nodes",
            "-days",
            "365",
            "-newkey",
            "rsa:4096",
            "-subj",
            "/O=Test Inc./CN=root",
            "-keyout",
            str(ca_dir / "root.key"),
            "-out",
            str(ca_dir / "root.crt"),
        ],
        check=True,
    )

    test_env = {
        "SAN_DNS_LIST": "minio.minio.svc.cluster.local",
        "ROOT_CA_CERT": str(ca_dir / "root.crt"),
        "ROOT_CA_KEY": str(ca_dir / "root.key"),
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run([str(role_dir / "main.sh")], env=env, capture_output=True, text=True)

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify certificate is signed by the provided CA
    cert_path = Path(role_env["ROLE_DIR"]) / role_env["CERT_NAME"]
    verify_result = subprocess.run(
        ["openssl", "verify", "-CAfile", str(ca_dir / "root.crt"), str(cert_path)], capture_output=True, text=True
    )
    assert verify_result.returncode == 0
    assert "OK" in verify_result.stdout


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_cert_generation_with_wildcard_dns(role_dir, role_env, setup_test_env):
    """Test Case 3: Certificate generation with wildcard DNS"""
    test_env = {"SAN_DNS_LIST": "*.minio.svc.cluster.local", "SAN_IP_LIST": ""}

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run([str(role_dir / "main.sh")], env=env, capture_output=True, text=True)

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify wildcard DNS in certificate
    cert_path = Path(role_env["ROLE_DIR"]) / role_env["CERT_NAME"]
    verify_result = subprocess.run(
        ["openssl", "x509", "-in", str(cert_path), "-text", "-noout"], capture_output=True, text=True
    )
    assert verify_result.returncode == 0
    assert "*.minio.svc.cluster.local" in verify_result.stdout


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_cert_generation_with_multiple_ips(role_dir, role_env, setup_test_env):
    """Test Case 4: Certificate generation with multiple IP addresses"""
    test_env = {"SAN_DNS_LIST": "", "SAN_IP_LIST": "192.168.1.1,10.0.0.1,172.16.0.1"}

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run([str(role_dir / "main.sh")], env=env, capture_output=True, text=True)

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Verify IP addresses in certificate
    cert_path = Path(role_env["ROLE_DIR"]) / role_env["CERT_NAME"]
    verify_result = subprocess.run(
        ["openssl", "x509", "-in", str(cert_path), "-text", "-noout"], capture_output=True, text=True
    )
    print(verify_result.stdout)
    assert verify_result.returncode == 0
    assert "IP Address:192.168.1.1" in verify_result.stdout
    assert "IP Address:10.0.0.1" in verify_result.stdout
    assert "IP Address:172.16.0.1" in verify_result.stdout


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_cert_generation_with_missing_ca_key(role_dir, setup_test_env, tmp_path):
    """Test Case 5: Error case - Certificate generation with missing CA key"""
    # Create only CA cert without key
    ca_dir = tmp_path / "ca"
    ca_dir.mkdir()

    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-sha256",
            "-nodes",
            "-days",
            "365",
            "-newkey",
            "rsa:4096",
            "-subj",
            "/O=Test Inc./CN=root",
            "-out",
            str(ca_dir / "root.crt"),
        ],
        check=True,
    )

    test_env = {
        "SAN_DNS_LIST": "test.example.com",
        "ROOT_CA_CERT": str(ca_dir / "root.crt"),
        "ROOT_CA_KEY": "",  # Missing key
    }

    env = setup_test_env(test_env)

    # Run the role
    result = subprocess.run([str(role_dir / "main.sh")], env=env, capture_output=True, text=True)

    # Should fail because ROOT_CA_KEY is not set
    assert result.stderr != ""
    assert "ROOT_CA_CERT is set but ROOT_CA_KEY is NOT set" in result.stderr


@pytest.mark.fvt
@pytest.mark.fvt_roles
def test_operator_install_default(role_dir, setup_test_env):
    """Test Case: Default operator install"""
    test_env = {
        # Add any environment variables needed for operator install here
    }
    env = setup_test_env(test_env)

    # Run the role's main.sh
    result = subprocess.run([str(role_dir / "main.sh")], env=env, capture_output=True, text=True)

    assert result.returncode == 0, f"Role execution failed: {result.stderr}"

    # Optionally, verify output files or logs
    # Example:
    # assert (Path(env["ROLE_DIR"]) / "some_expected_file").exists()
