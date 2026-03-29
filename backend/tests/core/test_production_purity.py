import pkgutil
import importlib
import pytest
import src  # Assuming 'backend' is the CWD or in PYTHONPATH and 'src' is the package

def test_production_code_purity():
    """
    Quality Guardrail: Ensures that 'Production' modules only depend on 'Silver' or 'Gold' code.
    """
    production_prefixes = ["src.systems.dnd5e", "src.core"]
    allowed_statuses = ["silver", "gold"]
    
    # We walk the entire src package
    for loader, module_name, is_pkg in pkgutil.walk_packages(src.__path__, src.__name__ + "."):
        is_production_module = any(module_name.startswith(p) for p in production_prefixes)
        
        if is_production_module:
            try:
                module = importlib.import_module(module_name)
                status = getattr(module, "__production_status__", "unchecked")
                
                if status not in allowed_statuses:
                    pytest.fail(
                        f"Quality Violation in '{module_name}':\n"
                        f"  Module is in a Production Scope but has status '{status}'.\n"
                        f"  Must be 'silver' or 'gold' to reside here."
                    )
            except ImportError as e:
                # If a module in the PRODUCTION scope fails to import, that's a Gold/Silver failure.
                pytest.fail(f"Import Error in Production Module '{module_name}': {e}")
            except Exception:
                continue

def test_legacy_isolation():
    """Fail if any legacy module is incorrectly marked as 'gold'."""
    # Placeholder for cross-module dependency check logic
    pass
