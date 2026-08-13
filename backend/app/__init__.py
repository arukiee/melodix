# Backend package initialization
import importlib, sys
# Alias top-level 'app' to this package for absolute imports
sys.modules.setdefault('app', importlib.import_module(__name__))
