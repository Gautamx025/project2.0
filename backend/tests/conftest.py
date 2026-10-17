import pytest
from fastapi.testclient import TestClient
from backend.app import config, main
from backend.app.repository import Repository

@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'ENV_FILE', tmp_path / '.env')
    monkeypatch.setenv('DATA_DIR', str(tmp_path/'data'))
    monkeypatch.setenv('DEMO_MODE', 'true')
    monkeypatch.setenv('REDIS_URL', '')
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://catalog.example.org')
    monkeypatch.setenv('STAGE_MAX_ATTEMPTS', '2')
    for field in config.SECRET_FIELDS:
        monkeypatch.delenv(field.upper(), raising=False)
    repo = Repository(config.settings().data_dir)
    monkeypatch.setattr(main, 'repository', repo)
    return repo

@pytest.fixture
def api():
    with TestClient(main.app) as instance:
        yield instance

@pytest.fixture
def ready(api):
    response = api.post('/api/jobs/sample', json={'sample': 'bottle'})
    assert response.status_code == 202, response.text
    return api.get('/api/jobs/'+response.json()['id']).json()
