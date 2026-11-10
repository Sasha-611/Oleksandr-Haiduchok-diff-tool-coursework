
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
build_dir = project_root / "out" / "build" / "x64-Debug"

sys.path.insert(0, str(build_dir))

import diff_core

result = diff_core.add(5, 3)

print(f"C++ result: {result}")
assert result == 8

print("C++ and Python integration test passed")
