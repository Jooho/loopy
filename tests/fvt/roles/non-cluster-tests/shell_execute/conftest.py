# tests/e2e/roles/test_shell_execute/conftest.py

import pytest
from pathlib import Path
from core.report_manager import LoopyReportManager


@pytest.fixture()
def role_name():
    """Fixture providing the path to the shell/execute role directory"""
    return "shell_execute"


@pytest.fixture()
def role_dir():
    """Fixture providing the path to the shell/execute role directory"""
    return Path("default_provided_services/roles/shell/execute")
