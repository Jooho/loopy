# tests/e2e/roles/conftest.py

import os
import json
import pytest
from pathlib import Path
from core.report_manager import LoopyReportManager

def pytest_sessionstart(session):
    """Initialize report manager before any tests start"""
    # Create a temporary directory for test results
    test_results_dir = Path("/tmp/loopy_test_results")
    test_results_dir.mkdir(exist_ok=True)
    
    # Initialize report manager
    report_manager = LoopyReportManager(str(test_results_dir))
    
    # Initialize role_time.json with required structure
    role_time_data = {
        "start_time": [],
        "end_time": []
    }
    role_time_file = test_results_dir / "role_time.json"
    with open(role_time_file, 'w') as f:
        json.dump(role_time_data, f)
    
    # Initialize summary.json with required structure
    summary_data = {
        "first_component_type": "role",
        "first_component_name": "cert-generate",
        "components": []
    }
    summary_file = test_results_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f)
    
    # Initialize report file
    report_file = test_results_dir / "report"
    with open(report_file, 'w') as f:
        f.write("# This is a report.\n")

@pytest.fixture(scope="class")
def role_dir():
    """Fixture providing the path to the role directory"""
    return Path("default_provided_services/roles")

@pytest.fixture(scope="class")
def output_dir(tmp_path_factory,generate_random_name):
    """Fixture providing a temporary directory for test outputs"""
    return tmp_path_factory.mktemp("/tmp/ms_cli/"+generate_random_name())

@pytest.fixture(scope="class")
def base_env(output_dir):
    """Fixture providing base environment variables needed for all tests"""
    return {
        "OUTPUT_ROOT_DIR": output_dir,
        "OUTPUT_REPORT_FILE": "report",
        "OUTPUT_DATE": "test",
        "OUTPUT_DIR": output_dir+"/output",
        "LOOPY_RESULT_DIR": output_dir+"/results",
        "SHOW_DEBUG_LOG": "false",
        "STOP_WHEN_FAILED": "false",
        "STOP_WHEN_ERROR_HAPPENED": "false",
        "ENABLE_LOOPY_LOG": "true"
    }