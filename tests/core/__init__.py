# tests/conftest.py 또는 tests/__init__.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
print("Jooho")
for p in sys.path:
    print(p)

import core.env
try:
    from core.env import EnvManager
    print("Jooho")
except ModuleNotFoundError as e:
    print(f"Error: {e}. Ensure 'src/core/env_loopy.py' exists and is correctly structured.")