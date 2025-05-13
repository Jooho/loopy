# tests/e2e/roles/test_cert_generate/test_cert_generate.py

import pytest
import subprocess
from pathlib import Path
import os


@pytest.mark.e2e
def test_cert_generate_command_line(role_dir, base_env):
    """Test the full command line behavior of cert-generate role"""
    # Test parameters
    san_dns = "minio.minio.svc.cluster.local,minio-minio.test"
    san_ip = "192.168.1.1"

    # Create a copy of the environment with PATH
    env = os.environ.copy()
    env.update(base_env)

    # Run the loopy command
    result = subprocess.run(
        [
            "./loopy",
            "roles",
            "run",
            "cert-generate",
            "-p",
            f"SAN_DNS_LIST={san_dns}",
            "-p",
            f"SAN_IP_LIST={san_ip}",
            "-l",
            "-g",
            "-r",
        ],
        capture_output=True,
        text=True,
        env=env,  # Add environment variables
    )

    # Print debug information
    print("\nCommand stdout:")
    print(result.stdout)
    print("\nCommand stderr:")
    print(result.stderr)

    # Verify command execution
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Get the output directory from the result
    output_dir = None
    for line in result.stdout.splitlines():
        print(f"Checking line: {line}")  # Debug print
        if "Loopy result dir:" in line:
            output_dir = line.split(":")[1].strip()
            break

    assert output_dir is not None, "Could not find output directory in command output"

    # Verify certificate files were generated
    role_dir = Path(output_dir) / "artifacts/cert-generate"
    assert role_dir.exists()

    # Check for required files
    assert (role_dir / "root.crt").exists()
    assert (role_dir / "root.key").exists()
    assert (role_dir / "custom.crt").exists()
    assert (role_dir / "custom.key").exists()

    # Verify certificate content
    verify_result = subprocess.run(
        ["openssl", "verify", "-CAfile", str(role_dir / "root.crt"), str(role_dir / "custom.crt")],
        capture_output=True,
        text=True,
    )
    assert verify_result.returncode == 0
    assert "OK" in verify_result.stdout

    # Verify environment variables were exported
    env_file = Path(output_dir) / "output/cert-generate.sh"
    assert env_file.exists()

    with open(env_file) as f:
        env_content = f.read()
        assert "ROOT_CA_CERT_FILE_PATH=" in env_content
        assert "ROOT_CA_KEY_FILE_PATH=" in env_content
        assert "CERT_FILE_PATH=" in env_content
        assert "KEY_FILE_PATH=" in env_content


# @pytest.mark.e2e
# def test_cert_generate_with_existing_ca(role_dir, base_env):
#     """Test cert-generate with existing CA certificate and key"""
#     # Create temporary directory for CA files
#     ca_dir = Path("/tmp/ca_test")
#     ca_dir.mkdir(exist_ok=True)

#     # Generate CA certificate and key
#     subprocess.run(
#         [
#             "openssl",
#             "req",
#             "-x509",
#             "-sha256",
#             "-nodes",
#             "-days",
#             "365",
#             "-newkey",
#             "rsa:4096",
#             "-subj",
#             "/O=Test Inc./CN=root",
#             "-keyout",
#             str(ca_dir / "root.key"),
#             "-out",
#             str(ca_dir / "root.crt"),
#         ],
#         check=True,
#     )

#     # Run the loopy command with existing CA
#     result = subprocess.run(
#         ["./loopy", "roles", "run", "cert-generate",
#          "-p", "SAN_DNS_LIST=test.example.com",
#          "-p", f"ROOT_CA_CERT={ca_dir}/root.crt",
#          "-p", f"ROOT_CA_KEY={ca_dir}/root.key"],
#         capture_output=True,
#         text=True
#     )

#     # Verify command execution
#     assert result.returncode == 0, f"Command failed: {result.stderr}"

#     # Get the output directory from the result
#     output_dir = None
#     for line in result.stdout.splitlines():
#         if "Loopy result dir:" in line:
#             output_dir = line.split(":")[1].strip()
#             break

#     assert output_dir is not None, "Could not find output directory in command output"

#     # Verify certificate was signed by the provided CA
#     role_dir = Path(output_dir) / "artifacts/cert-generate"
#     verify_result = subprocess.run(
#         ["openssl", "verify", "-CAfile", str(ca_dir / "root.crt"), str(role_dir / "custom.crt")],
#         capture_output=True,
#         text=True
#     )
#     assert verify_result.returncode == 0
#     assert "OK" in verify_result.stdout

# @pytest.mark.e2e
# def test_cert_generate_error_cases(role_dir, base_env):
#     """Test error cases for cert-generate"""
#     # Test missing required parameter
# @pytest.mark.e2e
# def test_cert_generate_with_existing_ca(role_dir, base_env):
#     """Test cert-generate with existing CA certificate and key"""
#     # Create temporary directory for CA files
#     ca_dir = Path("/tmp/ca_test")
#     ca_dir.mkdir(exist_ok=True)

#     # Generate CA certificate and key
#     subprocess.run(
#         [
#             "openssl",
#             "req",
#             "-x509",
#             "-sha256",
#             "-nodes",
#             "-days",
#             "365",
#             "-newkey",
#             "rsa:4096",
#             "-subj",
#             "/O=Test Inc./CN=root",
#             "-keyout",
#             str(ca_dir / "root.key"),
#             "-out",
#             str(ca_dir / "root.crt"),
#         ],
#         check=True,
#     )

#     # Run the loopy command with existing CA
#     result = subprocess.run(
#         ["./loopy", "roles", "run", "cert-generate",
#          "-p", "SAN_DNS_LIST=test.example.com",
#          "-p", f"ROOT_CA_CERT={ca_dir}/root.crt",
#          "-p", f"ROOT_CA_KEY={ca_dir}/root.key"],
#         capture_output=True,
#         text=True
#     )

#     # Verify command execution
#     assert result.returncode == 0, f"Command failed: {result.stderr}"

#     # Get the output directory from the result
#     output_dir = None
#     for line in result.stdout.splitlines():
#         if "Loopy result dir:" in line:
#             output_dir = line.split(":")[1].strip()
#             break

#     assert output_dir is not None, "Could not find output directory in command output"

#     # Verify certificate was signed by the provided CA
#     role_dir = Path(output_dir) / "artifacts/cert-generate"
#     verify_result = subprocess.run(
#         ["openssl", "verify", "-CAfile", str(ca_dir / "root.crt"), str(role_dir / "custom.crt")],
#         capture_output=True,
#         text=True
#     )
#     assert verify_result.returncode == 0
#     assert "OK" in verify_result.stdout

# @pytest.mark.e2e
# def test_cert_generate_error_cases(role_dir, base_env):
#     """Test error cases for cert-generate"""
#     # Test missing required parameter
#     result = subprocess.run(
#         ["./loopy", "roles", "run", "cert-generate"],
#         capture_output=True,
#         text=True
#     )
#     assert result.returncode != 0
#     assert "SAN_DNS_LIST" in result.stderr

#     # Test invalid CA key path
#     result = subprocess.run(
#         ["./loopy", "roles", "run", "cert-generate",
#          "-p", "SAN_DNS_LIST=test.example.com",
#          "-p", "ROOT_CA_CERT=/nonexistent/cert.crt",
#          "-p", "ROOT_CA_KEY=/nonexistent/key.key"],
#         capture_output=True,
#         text=True
#     )
#     assert result.returncode != 0
#     assert "file does not exist" in result.stderr
#     result = subprocess.run(
#         ["./loopy", "roles", "run", "cert-generate"],
#         capture_output=True,
#         text=True
#     )
#     assert result.returncode != 0
#     assert "SAN_DNS_LIST" in result.stderr

#     # Test invalid CA key path
#     result = subprocess.run(
#         ["./loopy", "roles", "run", "cert-generate",
#          "-p", "SAN_DNS_LIST=test.example.com",
#          "-p", "ROOT_CA_CERT=/nonexistent/cert.crt",
#          "-p", "ROOT_CA_KEY=/nonexistent/key.key"],
#         capture_output=True,
#         text=True
#     )
#     assert result.returncode != 0
#     assert "file does not exist" in result.stderr
