import pytest
from core.context import LoopyContext

@pytest.mark.fvt
@pytest.mark.core
def test_loopy_context(custom_context):
    config_dict = custom_context["config"]
    loopy_context = LoopyContext(custom_context)

    expected_result = {
        "default_vars": custom_context["default_vars"],
        "config": config_dict,
        "loopy_root_path": config_dict.get("loopy_root_path"),
        "role_list": config_dict.get("role_list", []),
        "unit_list": config_dict.get("unit_list", []),
        "playbook_list": config_dict.get("playbook_list", []),
        "logging": config_dict.get("logging", {}),
        "loopy_result_dir": config_dict.get("loopy_result_dir", ""),
    }

    assert loopy_context.role_list == expected_result.get(
        "role_list", {}
    ), f"Expected {expected_result.get('role_list',[])}, but got {loopy_context.role_list}"
    assert loopy_context.unit_list == expected_result.get(
        "unit_list", {}
    ), f"Expected {expected_result.get('unit_list',[])}, but got {loopy_context.unit_list}"
    assert loopy_context.playbook_list == expected_result.get(
        "playbook_list", {}
    ), f"Expected {expected_result.get('playbook_list',[])}, but got {loopy_context.playbook_list}"
    assert loopy_context.loopy_result_dir == expected_result.get(
        "loopy_result_dir", {}
    ), f"Expected {expected_result.get('loopy_result_dir','')}, but got {loopy_context.loopy_result_dir}"
    assert loopy_context.loopy_root_path == expected_result.get(
        "loopy_root_path", {}
    ), f"Expected {expected_result.get('loopy_root_path','')}, but got {loopy_context.loopy_root_path}"
    assert loopy_context.config == expected_result.get(
        "config", {}
    ), f"Expected {expected_result.get('config',{})}, but got {loopy_context.config}"
    assert loopy_context.default_vars == expected_result.get(
        "default_vars", {}
    ), f"Expected {expected_result.get('default_vars',{})}, but got {loopy_context.default_vars}"
    assert loopy_context.logging == expected_result.get(
        "logging", {}
    ), f"Expected {expected_result.get('logging',{})}, but got {loopy_context.logging}"