# tests/test_env.py
import os
import sys
from core.env import EnvManager

def test_env_manager_defaults(monkeypatch):
    monkeypatch.delenv("LOOPY_PATH", raising=False)
    monkeypatch.setenv("LOOPY_CONFIG_PATH", "custom.yaml")
    

    env = EnvManager()
    assert env.loopy_root_path == sys.path[0]
    assert env.loopy_config_path == "custom.yaml"
    assert "cli/commands" in env.commands_dir
    assert "commons/python" in env.py_utils_dir
