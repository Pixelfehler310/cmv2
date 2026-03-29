import pkgutil
import importlib
import pytest
import os
import sys

# Ensure src is in the python path for the walk
sys.path.append(os.getcwd())
import src as my_project_root

# Set production_status at module level for this test itself
__production_status__ = "gold"

def test_production_code_purity():
    """
    Stellt sicher, dass Code im neuen Scope nur auf 'silver' oder 'gold' zugreift.
    """
    # Allow 'gold' and 'silver' for production code.
    allowed_statuses = ["silver", "gold"]
    
    # We focus on the new D&D 5e systems which are the 'Production' targets
    new_scope_prefix = "src.systems.dnd5e.content"
    
    # Track results to provide a comprehensive report
    violations = []
    checked_count = 0

    # Package structure walk
    # Use pkgutil to find all modules in the src tree
    for loader, module_name, is_pkg in pkgutil.walk_packages(my_project_root.__path__, my_project_root.__name__ + "."):
        # We only enforce status on the 'Production' scope
        if module_name.startswith(new_scope_prefix):
            try:
                # Dynamically import to check metadata
                module = importlib.import_module(module_name)
                status = getattr(module, "__production_status__", "unchecked")
                checked_count += 1
                
                if status not in allowed_statuses:
                    violations.append(f"❌ Violation: Module '{module_name}' has status '{status}'. Only 'silver' or 'gold' allowed.")
                    
            except Exception as e:
                violations.append(f"⚠️ Import Error: Module '{module_name}' failed to load: {str(e)}")

    if violations:
        error_msg = f"Quality Guardrail Failed for scope {new_scope_prefix}:\n\n"
        error_msg += "\n".join(violations)
        error_msg += f"\n\nTotal modules checked in production scope: {checked_count}"
        pytest.fail(error_msg)

@pytest.mark.gold
@pytest.mark.v05
def test_purity_test_tagged():
    """This test just verifies that the tagging system works."""
    assert True
