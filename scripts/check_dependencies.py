#!/usr/bin/env python3
"""Script to check architectural dependencies compliance."""

import ast
import sys
from pathlib import Path


def check_imports():
    """Check that imports follow architectural rules."""
    src_path = Path(__file__).parent.parent / "src" / "task_context_mcp"

    violations = []

    for py_file in src_path.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue

        try:
            with py_file.open(encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module_parts = node.module.split(".") if node.module else []

                # Check layer dependencies
                if "models" in module_parts:
                    # Models should not import from other layers
                    forbidden_layers = ["business", "integrations", "entrypoints"]
                    if any(layer in module_parts for layer in forbidden_layers):
                        msg = f"{py_file}: models importing from {node.module}"
                        violations.append(msg)

                elif "business" in module_parts:
                    # Business should only import from models
                    forbidden_layers = ["integrations", "entrypoints"]
                    if any(layer in module_parts for layer in forbidden_layers):
                        msg = f"{py_file}: business importing from {node.module}"
                        violations.append(msg)

                elif "integrations" in module_parts:
                    # Integrations should not import from entrypoints
                    if "entrypoints" in module_parts:
                        msg = f"{py_file}: integrations importing from {node.module}"
                        violations.append(msg)

    if violations:
        print("Architecture violations found:")
        for violation in violations:
            print(f"  - {violation}")
        return False

    print("✓ Architecture dependencies are compliant")
    return True


if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)
