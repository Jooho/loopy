# tests/core/test_initializer.py

import os
import tempfile
import yaml
from core.initializer import Initializer


def test_initializer_creates_output_dirs(monkeypatch):
    # Configure default variables for a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        cli_config = {
            "cli": {
                "output_root_dir": tmpdir,
                "output_env_dir": "env",
                "output_artifacts_dir": "artifacts",
                "output_report_file": "report.md",
                "show_debug_log": "true",
                "stop_when_failed": "false",
                "stop_when_error_happened": "true"
            }
        }

        initializer = Initializer(cli_config)
        initializer.initialize()

        # Check if the output directories are created
        date_dirs = os.listdir(tmpdir)
        assert len(date_dirs) == 1

        date_dir = os.path.join(tmpdir, date_dirs[0])
        assert os.path.isdir(os.path.join(date_dir, "env"))
        assert os.path.isdir(os.path.join(date_dir, "artifacts"))
        assert os.path.isfile(os.path.join(date_dir, "report.md"))

        # Check if the environment variables are set correctly
        assert os.environ.get("OUTPUT_DIR") is not None
        assert os.environ.get("ARTIFACTS_DIR") is not None
        assert os.environ.get("SHOW_DEBUG_LOG") == "true"
