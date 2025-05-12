import os
import pytest
from unittest.mock import Mock, patch, mock_open
from colorama import Fore, Style
from cli.commands.loopy_report import (
    summary,
    get_playbook_table_row,
    get_unit_table_row,
    get_role_table_row,
    parse_report_file,
    flatten_components,
    format_time_and_result,
    update_results_from_report,
    shorten_string,
)


@pytest.fixture
def mock_report_manager():
    manager = Mock()
    manager.summary_dict = {
        "components": [],
        "first_component_type": "playbook",
        "first_component_name": "test_playbook",
    }
    return manager


@pytest.fixture
def sample_report_content():
    return """# This is a report.
0-cert-generate::0
1-cert-generate::0
2-shell-execute::command::1::0
2-shell-execute::command::2::0"""


@pytest.fixture
def sample_components():
    return {
        "type": "playbook",
        "name": "loopy-unit-tests-non-cluster-unit-role",
        "description": "This will test roles tests\n",
        "uuid": "6c0fd953-0ead-4b3d-808f-b002b570fb6b",
        "components": [
            {
                "type": "unit",
                "name": "loopy-roles-test-non-cluster-cert-generate",
                "description": 'This unit is to test role "cert-generate".',
                "uuid": "e28de9f9-3a9d-4d04-bb1c-8714d1c43e50",
                "components": [
                    {
                        "type": "role",
                        "name": "cert-generate",
                        "description": "[TEST] SAN_DNS_LIST parameter",
                        "artifacts_dir": "/tmp/ms_cli/djgst/artifacts/0-cert-generate",
                        "uuid": "925dd82c-6973-4cc5-87ca-f0873328080b",
                        "role_index": 0,
                        "commands": [
                            {
                                "name": "command-1",
                                "start_time": 1746762791.1144354,
                                "end_time": 1746762791.9944732,
                                "execution_time": 0.88,
                                "result": 0,
                            }
                        ],
                        "start_time": 1746762791.1144354,
                        "end_time": 1746762791.9944732,
                        "execution_time": 0.88,
                        "result": 0,
                    },
                    {
                        "type": "role",
                        "name": "cert-generate",
                        "description": "[TEST] SAN_IP_LIST parameter",
                        "artifacts_dir": "/tmp/ms_cli/djgst/artifacts/1-cert-generate",
                        "uuid": "923b466a-c5e2-4c6a-bd7d-80ba0afcad82",
                        "role_index": 1,
                        "commands": [
                            {
                                "name": "command-1",
                                "start_time": 1746762791.9987776,
                                "end_time": 1746762792.5428145,
                                "execution_time": 0.544,
                                "result": 0,
                            }
                        ],
                        "start_time": 1746762791.9987776,
                        "end_time": 1746762792.5428145,
                        "execution_time": 0.544,
                        "result": 0,
                    },
                ],
                "start_time": 1746762791.1144354,
                "end_time": 1746762792.5428145,
                "execution_time": 1.428,
                "result": 0,
            },
            {
                "type": "role",
                "name": "shell-execute",
                "description": "playbook-shell",
                "artifacts_dir": "/tmp/ms_cli/djgst/artifacts/2-shell-execute",
                "uuid": "340cac88-1a9a-402e-aacf-adcb160aed74",
                "role_index": 2,
                "commands": [
                    {
                        "name": "command-1",
                        "start_time": 1746762792.5742776,
                        "end_time": 1746762792.576728,
                        "execution_time": 0.002,
                        "result": 0,
                    },
                    {
                        "name": "command-2",
                        "start_time": 1746762792.577146,
                        "end_time": 1746762792.5799685,
                        "execution_time": 0.003,
                        "result": 0,
                    },
                ],
                "start_time": 1746762792.5742776,
                "end_time": 1746762792.5799685,
                "execution_time": 0.005,
                "result": 0,
            },
        ],
        "start_time": 1746762791.1144354,
        "end_time": 1746762792.5799685,
        "execution_time": 1.466,
        "result": 0,
    }


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_shorten_string():
    # Test string shorter than max length
    assert shorten_string("test", 10) == "test"

    # Test string equal to max length
    assert shorten_string("test", 4) == "test"

    # Test string longer than max length
    assert shorten_string("test_string", 8) == "test_..."


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_format_time_and_result():
    # Test successful result
    time, result = format_time_and_result(65.5, 0)
    assert time == "1min 5.5"
    assert result == "Success"

    # Test failed result
    time, result = format_time_and_result(30.0, 1)
    assert time == "0min 30.0"
    assert result == "Fail"


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_parse_report_file(sample_report_content):
    with patch("builtins.open", mock_open(read_data=sample_report_content)):
        result = parse_report_file("dummy_path")
        assert result == [
            "0-cert-generate::0",
            "1-cert-generate::0",
            "2-shell-execute::command::1::0",
            "2-shell-execute::command::2::0",
        ]


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_get_playbook_table_row():
    component = {
        "type": "playbook",
        "name": "test_playbook",
        "description": "Test Playbook",
        "result_str": "Success",
        "execution_time": 60,
        "formatted_execution_time": "1min 0.0",
    }

    options = {
        "show_index": True,
        "show_type": True,
        "show_name": True,
        "show_result": True,
        "show_time": True,
        "show_folder": True,
    }

    row = get_playbook_table_row(0, component, options)
    assert len(row) == 6
    assert Fore.YELLOW in row[0]  # Index color
    assert "playbook" in row[1]
    assert "Test Playbook" in row[2]
    assert Fore.GREEN in row[3]  # Success color
    assert "1min 0.0" in row[4]


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_get_unit_table_row():
    component = {
        "type": "unit",
        "name": "test_unit",
        "description": "Test Unit",
        "result_str": "Success",
        "execution_time": 30,
        "formatted_execution_time": "0min 30.0",
    }

    options = {
        "show_index": True,
        "show_type": True,
        "show_name": True,
        "show_result": True,
        "show_time": True,
        "show_folder": True,
    }

    row = get_unit_table_row(0, component, options)
    assert len(row) == 6
    assert Fore.MAGENTA in row[0]  # Index color
    assert "unit" in row[1]
    assert "Test Unit" in row[2]
    assert Fore.GREEN in row[3]  # Success color
    assert "0min 30.0" in row[4]


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_get_role_table_row():
    component = {
        "type": "role",
        "name": "test_role",
        "description": "Test Role",
        "result_str": "Success",
        "execution_time": 45,
        "formatted_execution_time": "0min 45.0",
        "artifacts_dir": "/tmp/artifacts",
        "commands": [{"name": "command1", "description": "Test Command 1", "execution_time": 20, "result": 0}],
    }

    options = {
        "show_index": True,
        "show_type": True,
        "show_name": True,
        "show_result": True,
        "show_time": True,
        "show_folder": True,
    }

    rows = get_role_table_row(0, component, "playbook", options)
    assert len(rows) == 1  # Only role row since there's only one command
    assert "role" in rows[0][1]
    assert "Test Role" in rows[0][2]
    assert Fore.GREEN in rows[0][3]  # Success color
    assert "/tmp/artifacts" in rows[0][5]


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_flatten_components(sample_components):
    flat_list = flatten_components(sample_components, [])
    assert len(flat_list) == 5
    assert flat_list[0]["type"] == "playbook"
    assert flat_list[1]["type"] == "unit"
    assert flat_list[2]["type"] == "role"
    assert flat_list[3]["type"] == "role"
    assert flat_list[4]["type"] == "role"
    assert "formatted_execution_time" in flat_list[2]
    assert "result_str" in flat_list[2]


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
@patch("cli.commands.loopy_report.LoopyReportManager")
def test_summary(mock_report_manager_class, mock_loopy_ctx, sample_report_content, sample_components):
    # Setup mock report manager
    mock_report_manager = Mock()
    mock_report_manager_class.return_value = mock_report_manager
    mock_report_manager.summary_dict = {
        "components": sample_components,
        "first_component_type": "Playbook",
        "first_component_name": "loopy-unit-tests-non-cluster-unit-role",
    }

    # Mock the report file path
    report_path = os.path.join(mock_loopy_ctx.obj.loopy_result_dir, "report")

    # Mock file operations
    with patch("builtins.open", mock_open(read_data=sample_report_content)) as mock_file:
        # Mock os.path.join to return our mocked path
        with patch("os.path.join", return_value=report_path):
            summary(mock_loopy_ctx)

            # Verify report file was opened
            mock_file.assert_called_once_with(report_path, "r")

            # Verify report manager methods were called
            assert (
                mock_report_manager.load_summary.call_count == 2
            )  # Called twice: once in summary() and once in update_results_from_report()
            mock_report_manager.update_summary.assert_called_once_with("components", sample_components)


@pytest.mark.cli
@pytest.mark.cli_report
@pytest.mark.non_cluster_tests
def test_update_results_from_report(mock_report_manager, sample_report_content, sample_components):
    mock_report_manager.summary_dict["components"] = sample_components

    with patch("builtins.open", mock_open(read_data=sample_report_content)):
        update_results_from_report(mock_report_manager, [sample_report_content], sample_components)
        mock_report_manager.load_summary.assert_called_once()
        mock_report_manager.update_summary.assert_called_once()
