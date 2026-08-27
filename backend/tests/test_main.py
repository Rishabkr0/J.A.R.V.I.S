from fastapi.testclient import TestClient
from app.main import app
from app.events.models import JarvisState
from app.security.permissions import PermissionLevel

client = TestClient(app)

def test_health():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'

def test_event_models():
    assert JarvisState.IDLE == 'IDLE'

def test_permissions():
    assert PermissionLevel.SAFE == 'SAFE'
