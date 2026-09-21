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

    assert result == [{'email': 'participant@example.com', 'displayName': '参加者'}]


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

    response = app.download_csv()

    assert response.status_code == 200
    csv_text = response.get_data(as_text=True)
    assert 'participantId,displayName' in csv_text
    assert '123,山田太郎' in csv_text
