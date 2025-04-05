# tests/core/test_config_loader.py

import tempfile
import yaml
from core.config_loader import ConfigLoader


def test_config_loader_reads_both_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        # config.yaml
        config_path = f"{tmpdir}/config.yaml"
        default_vars_path = f"{tmpdir}/default_vars.yaml"

        config_data = {"default_vars_file": "default_vars.yaml"}
        default_vars = {
            "cli": {
                "output_root_dir": "/tmp/output",
                "output_env_dir": "env",
                "output_artifacts_dir": "artifacts",
                "output_report_file": "report.md",
                "show_debug_log": "true",
                "stop_when_failed": "false",
                "stop_when_error_happened": "true"
            }
        }

        with open(config_path, "w") as f:
            yaml.safe_dump(config_data, f)

        with open(default_vars_path, "w") as f:
            yaml.safe_dump(default_vars, f)

        loader = ConfigLoader(config_path=config_path, root_path=tmpdir)
        loader.load()

        assert loader.get_config() == config_data
        assert loader.get_default_vars()["cli"]["output_root_dir"] == "/tmp/output"
