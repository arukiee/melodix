import os, json

# Ensure imports resolve to the project root
project_root = os.path.abspath('Desktop/ps')
os.environ['PYTHONPATH'] = project_root

# Import FastAPI app and seed script
from backend.app.main import app
from backend.scripts.seed_curriculum import seed_data

# Seed the SQLite DB with demo data
seed_data()

# Use FastAPI TestClient for in‑process requests
from fastapi.testclient import TestClient
client = TestClient(app)

# Verify list endpoint
list_resp = client.get('/api/v1/curriculum/paths')
print('LIST STATUS', list_resp.status_code)
print('LIST BODY', json.dumps(list_resp.json(), indent=2))

if list_resp.status_code == 200 and list_resp.json():
    first_item = list_resp.json()[0] if isinstance(list_resp.json(), list) else list_resp.json()
    first_id = first_item.get('id')
    detail_resp = client.get(f'/api/v1/curriculum/paths/{first_id}')
    print('DETAIL STATUS', detail_resp.status_code)
    print('DETAIL BODY', json.dumps(detail_resp.json(), indent=2))
else:
    print('No data returned from list endpoint')
