import json
import os
import random
from csv import writer as csv_writer
from io import StringIO

import gspread
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from google.oauth2.service_account import Credentials

app = Flask(__name__, static_folder='.')
CORS(app, resources={r"/*": {"origins": "*"}})

ASSIGNMENTS_FILE = 'assignments.json'
REGISTERED_ACCOUNTS_FILE = 'registered_accounts.json'


def load_assignments():
    """参加者IDの割り当て情報を読み込みます。"""
    if not os.path.exists(ASSIGNMENTS_FILE):
        return {}

    try:
        with open(ASSIGNMENTS_FILE, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {}
    except Exception as error:
        print(f'割り当て情報読み込みエラー: {error}')
        return {}


def save_assignments(assignments):
    """参加者IDの割り当て情報を保存します。"""
    with open(ASSIGNMENTS_FILE, 'w', encoding='utf-8') as handle:
        json.dump(assignments, handle, ensure_ascii=False, indent=2)


def load_registered_accounts():
    """登録済みアカウント一覧を読み込みます。"""
    if not os.path.exists(REGISTERED_ACCOUNTS_FILE):
        return []

    try:
        with open(REGISTERED_ACCOUNTS_FILE, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            return data if isinstance(data, list) else []
    except Exception as error:
        print(f'登録アカウント読み込みエラー: {error}')
        return []


def save_registered_accounts(accounts):
    """登録済みアカウント一覧を保存します。"""
    with open(REGISTERED_ACCOUNTS_FILE, 'w', encoding='utf-8') as handle:
        json.dump(accounts, handle, ensure_ascii=False, indent=2)


def assign_balanced_ids(register_emails):
    """登録済みメールアドレスに 100〜199 と 200〜299 を均等にランダム割り当てします。"""
    if not register_emails:
        return {}

    if len(register_emails) % 2 != 0:
        raise ValueError('登録アカウント数が偶数でないため、均等割り当てできません。')

    shuffled_emails = list(register_emails)
    random.shuffle(shuffled_emails)

    half = len(shuffled_emails) // 2
    low_emails = shuffled_emails[:half]
    high_emails = shuffled_emails[half:]

    low_ids = list(range(100, 200))
    high_ids = list(range(200, 300))
    random.shuffle(low_ids)
    random.shuffle(high_ids)

    assignments = {}
    for email, participant_id in zip(low_emails, low_ids[:len(low_emails)]):
        assignments[email] = str(participant_id)

    for email, participant_id in zip(high_emails, high_ids[:len(high_emails)]):
        assignments[email] = str(participant_id)

    return assignments

# --- Google Sheets 連携 ---

def get_sheet():
    """Google Sheets の responses ワークシートを取得します。"""
    try:
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')

        if os.path.exists('service_account.json'):
            credentials = Credentials.from_service_account_file(
                'service_account.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
        else:
            service_account_json = os.environ.get('SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                return None
            credentials = Credentials.from_service_account_info(
                json.loads(service_account_json),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        if not sheet_id:
            return None

        client = gspread.authorize(credentials)
        return client.open_by_key(sheet_id).worksheet('responses')
    except Exception as error:
        print(f'Sheet接続エラー: {error}')
        return None


def append_to_sheet(data):
    """Google Sheets にデータを追加します。"""
    try:
        sheet = get_sheet()
        if not sheet:
            print('Sheetが利用できません')
            return False

        row = [
            data.get('participantId', ''),
            data.get('learnType', ''),
            data.get('answerType', ''),
            data.get('totalCorrect', ''),
            data.get('totalTimeSec', ''),
            data.get('timestamp', ''),
            json.dumps(data.get('questions', []), ensure_ascii=False)
        ]

        sheet.append_row(row)
        print('Sheet追加成功')
        return True
    except Exception as error:
        print(f'Sheet追加エラー: {error}')
        return False


@app.get('/health')
def health():
    return 'ok', 200


@app.get('/')
def home():
    return send_from_directory('.', 'index.html')


@app.get('/login')
def login_page():
    return send_from_directory('.', 'login.html')


@app.get('/test')
def test_page():
    return send_from_directory('.', 'test.html')


@app.get('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')


@app.get('/finish')
def finish_page():
    return send_from_directory('.', 'finish.html')


@app.get('/<path:path>')
def static_files(path):
    if os.path.isfile(path):
        return send_from_directory('.', path)
    return 'File not found', 404


@app.post('/register-account')
def register_account():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'status': 'error', 'message': 'メールアドレスが必要です。'}), 400

    registered_accounts = load_registered_accounts()
    if email not in registered_accounts:
        registered_accounts.append(email)
        save_registered_accounts(registered_accounts)

    assignments = load_assignments()
    if email in assignments:
        return jsonify({'status': 'ok', 'participantId': assignments[email], 'assigned': True, 'pending': False})

    return jsonify({'status': 'ok', 'participantId': None, 'assigned': False, 'pending': True, 'registeredCount': len(registered_accounts)})


@app.get('/assignments-status')
def assignments_status():
    assignments = load_assignments()
    registered_accounts = load_registered_accounts()
    assigned_ids = [int(value) for value in assignments.values() if str(value).isdigit()]
    low_count = sum(1 for value in assigned_ids if 100 <= value <= 199)
    high_count = sum(1 for value in assigned_ids if 200 <= value <= 299)

    return jsonify({
        'registeredCount': len(registered_accounts),
        'assignedCount': len(assignments),
        'pendingCount': max(0, len(registered_accounts) - len(assignments)),
        'lowCount': low_count,
        'highCount': high_count,
        'remaining': max(0, len(registered_accounts) - len(assignments))
    })


@app.post('/admin/register-email')
def admin_register_email():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'status': 'error', 'message': 'メールアドレスが必要です。'}), 400

    registered_accounts = load_registered_accounts()
    if email not in registered_accounts:
        registered_accounts.append(email)
        save_registered_accounts(registered_accounts)

    return jsonify({'status': 'ok', 'registeredCount': len(registered_accounts)})


@app.post('/admin/assign-ids')
def admin_assign_ids():
    registered_accounts = load_registered_accounts()
    if not registered_accounts:
        return jsonify({'status': 'error', 'message': '登録済みアカウントがありません。'}), 400

    if len(registered_accounts) % 2 != 0:
        return jsonify({'status': 'error', 'message': '登録アカウント数が偶数でないため、均等割り当てできません。'}), 400

    assignments = assign_balanced_ids(registered_accounts)
    save_assignments(assignments)
    return jsonify({'status': 'ok', 'assignments': assignments})


@app.post('/admin/manual-assign')
def admin_manual_assign():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    participant_id = (data.get('participantId') or '').strip()

    if not email or not participant_id:
        return jsonify({'status': 'error', 'message': 'メールアドレスと参加者IDが必要です。'}), 400

    if not participant_id.isdigit():
        return jsonify({'status': 'error', 'message': '参加者IDは数字で指定してください。'}), 400

    participant_id_number = int(participant_id)
    if not (100 <= participant_id_number <= 299):
        return jsonify({'status': 'error', 'message': '参加者IDは100〜299の範囲で指定してください。'}), 400

    assignments = load_assignments()
    assignments[email] = str(participant_id_number)
    save_assignments(assignments)

    registered_accounts = load_registered_accounts()
    if email not in registered_accounts:
        registered_accounts.append(email)
        save_registered_accounts(registered_accounts)

    return jsonify({'status': 'ok', 'participantId': participant_id_number})


@app.post('/admin/reset-assignments')
def reset_assignments():
    save_assignments({})
    save_registered_accounts([])
    return jsonify({'status': 'ok'})


@app.post('/submit')
def submit():
    data = request.get_json(silent=True) or {}
    filename = 'results.json'

    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.append(data)

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    if not append_to_sheet(data):
        print('Sheet追加に失敗しました。submit()はエラーを返します。')
        return jsonify({'status': 'error', 'message': 'Google Sheetsへの追加に失敗しました。'}), 500

    return jsonify({'status': 'ok'})


@app.get('/results')
def get_results():
    filename = 'results.json'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify([])


@app.route('/download_csv')
def download_csv():
    filename = 'results.json'
    if not os.path.exists(filename):
        return 'No data', 404

    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)

    output = StringIO()
    writer = csv_writer(output)

    writer.writerow([
        'participantId', 'learnType', 'answerType', 'condition', 'totalTimeSec', 'totalCorrect',
        'questionId', 'questionText', 'correctAnswer', 'participantAnswer', 'correct', 'timeSec', 'timestamp'
    ])

    for entry in data:
        for question in entry.get('questions', []):
            writer.writerow([
                entry.get('participantId', ''),
                entry.get('learnType', ''),
                entry.get('answerType', ''),
                entry.get('condition', ''),
                entry.get('totalTimeSec', ''),
                entry.get('totalCorrect', ''),
                question.get('id', ''),
                question.get('text', ''),
                question.get('correctAnswer', ''),
                question.get('participantAnswer', ''),
                question.get('correct', ''),
                question.get('timeSec', ''),
                entry.get('timestamp', '')
            ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=results.csv'}
    )


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
