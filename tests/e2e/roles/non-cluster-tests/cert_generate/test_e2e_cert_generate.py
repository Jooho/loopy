# tests/e2e/roles/test_cert_generate/test_cert_generate.py

import pytest
import subprocess
from pathlib import Path
import os


@pytest.mark.e2e
@pytest.mark.e2e_roles
@pytest.mark.non_cluster_tests
def test_cert_generate(role_env):
    """Test the full command line behavior of cert-generate role"""

    # Create a copy of the environment with PATH
    env = os.environ.copy()
    # This is for debugging purposes in subprocesses
    # env["LOOPY_DEBUG"] = "1"
    env.update(role_env)

    # Run the loopy command
    result = subprocess.run(
        [
            "./loopy",
            "roles",
            "run",
            "cert-generate",
            "-p",
            f"SAN_DNS_LIST={role_env['SAN_DNS_LIST']}",
            "-p",
            f"SAN_IP_LIST={role_env['SAN_IP_LIST']}",
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

    # Verify certificate files were generated
    output_dir = Path(role_env["LOOPY_OUTPUT_ROOT_DIR"]) / role_env["LOOPY_OUTPUT_TARGET_DIR"]
    role_dir = output_dir / "artifacts/cert-generate"
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
    env_file = output_dir / "output/0-cert-generate-output.sh"
    assert env_file.exists()

    with open(env_file) as f:
        env_content = f.read()
        assert "ROOT_CA_CERT_FILE_PATH=" in env_content
        assert "ROOT_CA_KEY_FILE_PATH=" in env_content
        assert "CERT_FILE_PATH=" in env_content
        assert "KEY_FILE_PATH=" in env_content

