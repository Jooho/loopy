import pytest
import subprocess
import os
from tests.conftest import timeout
from pathlib import Path

@pytest.mark.e2e
@pytest.mark.e2e_roles
@pytest.mark.cluster_tests
def test_minio_deploy_default(role_env):
    """Test the full command line behavior of minio-deploy role"""
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
            "minio-deploy",                    
            "-l",
            "-g",
            "-r",
        ],
        capture_output=True,
        text=True,
        env=env,  # Add environment variables
    )

    # Verify command execution
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    result = subprocess.run(
        [
            "oc",
            "wait",
            "--for=condition=Ready",
            "pod",
            "-l",
            role_env["MINIO_LABEL"],
            "-n",
            role_env["MINIO_NAMESPACE"],
            f"--timeout={timeout}s",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Operator pod not ready: {result.stderr}"
    assert "condition met" in result.stdout, f"'condition met' not found in output: {result.stdout}"

    # Verify environment variables were exported
    output_dir = Path(role_env["LOOPY_OUTPUT_ROOT_DIR"]) / role_env["LOOPY_OUTPUT_TARGET_DIR"]
    env_file = output_dir / "output/0-minio-deploy-output.sh"
    assert env_file.exists()

    with open(env_file) as f:
        env_content = f.read()    
        assert "MINIO_S3_SVC_URL=" in env_content
        assert "MINIO_DEFAULT_BUCKET_NAME=" in env_content
        assert "MINIO_ACCESS_KEY_ID=" in env_content
        assert "MINIO_SECRET_ACCESS_KEY=" in env_content
        assert "MINIO_REGION=" in env_content
