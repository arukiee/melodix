import sys, os
sys.path.append(os.path.abspath('backend'))
try:
    import app.core.database as db
    print('Import succeeded')
except Exception as e:
    print('Import failed:', e)
