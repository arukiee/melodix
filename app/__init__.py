import importlib, sys, pathlib
# Ensure the backend app package path is on sys.path
_backend_path = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app"
if str(_backend_path.parent) not in sys.path:
    sys.path.insert(0, str(_backend_path.parent))
# Import the actual backend.app module
_backend = importlib.import_module('backend.app')
# Expose it as the top-level 'app' package
sys.modules[__name__] = _backend
