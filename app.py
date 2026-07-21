import json
import os
from csv import writer as csv_writer
from io import StringIO

import gspread
from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from google.oauth2.service_account import Credentials

app = Flask(__name__, static_folder='.')
CORS(app)

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


@app.get('/<path:path>')
def static_files(path):
    if os.path.isfile(path):
        return send_from_directory('.', path)
    return 'File not found', 404


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
