import json

import app


class DummyUser:
    def __init__(self, custom_claims=None):
        self.custom_claims = custom_claims or {}


def test_filter_registered_accounts_excludes_admins():
    accounts = [
        {'email': 'admin@example.com', 'displayName': '管理者'},
        {'email': 'participant@example.com', 'displayName': '参加者'},
    ]

    original = app.is_admin_email
    try:
        app.is_admin_email = lambda email: email == 'admin@example.com'
        result = app.filter_registered_accounts(accounts)
    finally:
        app.is_admin_email = original

    assert result == [{'email': 'participant@example.com', 'displayName': '参'}]


def test_register_account_rejects_admin_login():
    client = app.app.test_client()

    original = app.verify_id_token
    original_is_admin = app.is_admin_email
    try:
        app.verify_id_token = lambda: {'email': 'admin@example.com', 'name': '管理者', 'admin': True}
        app.is_admin_email = lambda email: False
        response = client.post(
            '/register-account',
            headers={'Authorization': 'Bearer test-token'},
            json={'displayName': '管理者'}
        )
    finally:
        app.verify_id_token = original
        app.is_admin_email = original_is_admin

    assert response.status_code == 403
    assert response.get_json()['status'] == 'error'


def test_register_account_allows_non_admin_token_even_if_email_lookup_fails():
    client = app.app.test_client()

    original = app.verify_id_token
    original_is_admin = app.is_admin_email
    try:
        app.verify_id_token = lambda: {'email': 'participant@example.com', 'name': '参加者', 'admin': False}
        app.is_admin_email = lambda email: True
        response = client.post(
            '/register-account',
            headers={'Authorization': 'Bearer test-token'},
            json={'displayName': '参加者'}
        )
    finally:
        app.verify_id_token = original
        app.is_admin_email = original_is_admin

    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


def test_register_account_stores_only_first_display_name_character(monkeypatch):
    client = app.app.test_client()
    saved_accounts = []
    monkeypatch.setattr(app, 'verify_id_token', lambda: {
        'email': 'participant@example.com',
        'name': '参加者氏名',
        'admin': False,
    })
    monkeypatch.setattr(app, 'load_registered_accounts', lambda: [])
    monkeypatch.setattr(app, 'save_registered_accounts', saved_accounts.append)
    monkeypatch.setattr(app, 'load_assignments', lambda: {})

    response = client.post('/register-account', json={'displayName': '別の表示名'})

    assert response.status_code == 200
    assert saved_accounts[0][0]['displayName'] == '参'


def test_submit_stores_only_first_display_name_character(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sheet_records = []
    monkeypatch.setattr(app, 'verify_id_token', lambda: {
        'email': 'participant@example.com',
        'name': '山田太郎',
        'admin': False,
    })
    monkeypatch.setattr(app, 'load_assignments', lambda: {'participant@example.com': '123'})
    monkeypatch.setattr(app, 'append_to_sheet', lambda data: sheet_records.append(data.copy()) or True)

    response = app.app.test_client().post('/submit', json={
        'participantId': '123',
        'displayName': '山田太郎',
        'learnType': 'digital',
        'answerType': 'digital',
        'condition': 'tampered',
        'questions': [],
    })

    saved_records = json.loads((tmp_path / 'results.json').read_text(encoding='utf-8'))
    assert response.status_code == 200
    assert saved_records[0]['displayName'] == '山'
    assert saved_records[0]['learnType'] == 'analog'
    assert saved_records[0]['answerType'] == 'analog'
    assert saved_records[0]['condition'] == 'analog_learn_analog_answer'
    assert sheet_records[0]['displayName'] == '山'


def test_submit_truncates_display_name_from_firebase_token(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    sheet_records = []
    monkeypatch.setattr(app, 'verify_id_token', lambda: {
        'email': 'participant@example.com',
        'name': '佐藤花子',
    })
    monkeypatch.setattr(app, 'load_assignments', lambda: {'participant@example.com': '124'})
    monkeypatch.setattr(app, 'append_to_sheet', lambda data: sheet_records.append(data.copy()) or True)

    response = app.app.test_client().post('/submit', json={'participantId': '124', 'questions': []})

    saved_records = json.loads((tmp_path / 'results.json').read_text(encoding='utf-8'))
    assert response.status_code == 200
    assert saved_records[0]['displayName'] == '佐'
    assert sheet_records[0]['displayName'] == '佐'


def test_submit_rejects_missing_authentication(monkeypatch):
    monkeypatch.setattr(app, 'verify_id_token', lambda: None)

    response = app.app.test_client().post('/submit', json={'participantId': '123'})

    assert response.status_code == 401


def test_submit_rejects_another_participants_id(monkeypatch):
    monkeypatch.setattr(app, 'verify_id_token', lambda: {'email': 'participant@example.com'})
    monkeypatch.setattr(app, 'load_assignments', lambda: {'participant@example.com': '123'})

    response = app.app.test_client().post('/submit', json={'participantId': '124'})

    assert response.status_code == 403


def test_static_files_only_serve_allowlisted_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'style.css').write_text('body {}', encoding='utf-8')
    (tmp_path / 'app.py').write_text('secret source', encoding='utf-8')
    (tmp_path / 'results.json').write_text('[]', encoding='utf-8')

    client = app.app.test_client()

    assert client.get('/style.css').status_code == 200
    assert client.get('/app.py').status_code == 404
    assert client.get('/results.json').status_code == 404
    assert client.get('/registered_accounts.json').status_code == 404


def test_results_requires_admin_auth(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'results.json').write_text('[]', encoding='utf-8')
    client = app.app.test_client()

    assert client.get('/results').status_code == 401

    monkeypatch.setattr(app, 'verify_id_token', lambda: {'admin': True})
    response = client.get('/results')

    assert response.status_code == 200
    assert response.get_json() == []


def test_append_to_sheet_preserves_original_columns(monkeypatch):
    class DummySheet:
        def append_row(self, row):
            self.row = row

    sheet = DummySheet()
    monkeypatch.setattr(app, 'get_sheet', lambda: sheet)

    result = app.append_to_sheet({
        'participantId': '123',
        'displayName': '山田太郎',
        'learnType': 'analog',
        'answerType': 'digital',
        'condition': 'analog_learn_digital_answer',
        'totalTimeSec': 12.5,
        'totalCorrect': 3,
        'timestamp': '2026-09-29T00:00:00Z',
        'questions': [],
    })

    assert result is True
    assert sheet.row == [
        '123', '山', 'analog', 'digital', 3, 12.5,
        '2026-09-29T00:00:00Z', '[]'
    ]


def test_download_csv_includes_display_name_after_participant_id(tmp_path, monkeypatch):
    payload = [{
        'participantId': '123',
        'displayName': '山田太郎',
        'learnType': 'analog',
        'answerType': 'analog',
        'condition': 'control',
        'totalTimeSec': 10,
        'totalCorrect': 1,
        'questions': [{
            'id': '1',
            'text': 'Q1',
            'correctAnswer': '1',
            'participantAnswer': '1',
            'correct': True,
            'timeSec': 2,
        }],
        'timestamp': '2024-01-01T00:00:00Z',
    }]
    data_file = tmp_path / 'results.json'
    data_file.write_text(json.dumps(payload), encoding='utf-8')
    monkeypatch.chdir(tmp_path)
    client = app.app.test_client()

    assert client.get('/download_csv').status_code == 401

    monkeypatch.setattr(app, 'verify_id_token', lambda: {'admin': True})
    response = client.get('/download_csv')

    assert response.status_code == 200
    csv_text = response.get_data(as_text=True)
    assert 'participantId,displayName' in csv_text
    assert '123,山' in csv_text
