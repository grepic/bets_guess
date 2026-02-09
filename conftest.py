"""Root conftest — ensure packages are importable."""
import sys
from pathlib import Path

# Add project root to sys.path so 'packages' and 'apps' are importable
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
