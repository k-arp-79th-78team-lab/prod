from flask import Flask, send_from_directory, request, jsonify, Response
from flask_cors import CORS
import os
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__, static_folder='.')
CORS(app)

# --- Google Sheets 連携 ---
def get_sheet():
    """Google Sheetを取得"""
    try:
        # 環境変数からSHEET_IDと認証情報を取得
        sheet_id = os.environ.get("GOOGLE_SHEET_ID")
        
        # ローカル開発用: service_account.jsonがあればそれを使用
        if os.path.exists("service_account.json"):
            creds = Credentials.from_service_account_file(
                "service_account.json",
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        else:
            # 本番環境: 環境変数から認証情報を取得
            service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
            if not service_account_json:
                return None
            creds = Credentials.from_service_account_info(
                json.loads(service_account_json),
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
        
        if not sheet_id:
            return None
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id).worksheet("responses")
        return sheet
    except Exception as e:
        print(f"Sheet接続エラー: {e}")
        return None

def append_to_sheet(data):
    """Google Sheetにデータを追加"""
    try:
        sheet = get_sheet()
        if not sheet:
            print("Sheetが利用できません")
            return False
        
        # 追加する行を作成
        row = [
            data.get("participantId", ""),
            data.get("learnType", ""),
            data.get("answerType", ""),
            data.get("totalCorrect", ""),
            data.get("totalTimeSec", ""),
            data.get("timestamp", ""),
            json.dumps(data.get("questions", []), ensure_ascii=False)
        ]
        
        sheet.append_row(row)
        print("Sheet追加成功")
        return True
    except Exception as e:
        print(f"Sheet追加エラー: {e}")
        return False

@app.get("/health")
def health():
    return "ok", 200

# --- 静的ファイル ---
@app.get("/")
def home():
    return send_from_directory('.', 'index.html')

@app.get("/<path:path>")
def static_files(path):
    if os.path.isfile(path):
        return send_from_directory('.', path)
    else:
        return "File not found", 404

@app.get("/favicon.ico")
def favicon():
    return "", 204

# --- 結果保存 ---
@app.post("/submit")
def submit():
    data = request.get_json()
    filename = "results.json"

    # 既存データ読み込み
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    # 新しいデータを追加
    existing_data.append(data)

    # 保存
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)

    # Google Sheetsにも追加
    sheet_result = append_to_sheet(data)
    if not sheet_result:
        print("Sheet追加に失敗しました。submit()はエラーを返します。")
        return jsonify({"status": "error", "message": "Google Sheetsへの追加に失敗しました。"}), 500

    return jsonify({"status": "ok"})

# --- 結果取得 ---
@app.get("/results")
def get_results():
    filename = "results.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    else:
        return jsonify([])

@app.route("/download_csv")
def download_csv():
    filename = "results.json"

    if not os.path.exists(filename):
        return "No data", 404

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # CSV を文字列として作成
    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.writer(output)

    # ヘッダー
    writer.writerow([
        "participantId", "learnType", "answerType", "condition", "totalTimeSec", "totalCorrect",
        "questionId", "questionText", "correctAnswer", "participantAnswer", "correct", "timeSec", "timestamp"
    ])

    # 各 participant のデータを展開して書き込む
    for entry in data:
        for q in entry.get("questions", []):
            writer.writerow([
                entry.get("participantId", ""),
                entry.get("learnType", ""),
                entry.get("answerType", ""),
                entry.get("condition", ""),
                entry.get("totalTimeSec", ""),
                entry.get("totalCorrect", ""),
                q.get("id", ""),
                q.get("text", ""),
                q.get("correctAnswer", ""),
                q.get("participantAnswer", ""),
                q.get("correct", ""),
                q.get("timeSec", ""),
                entry.get("timestamp", "")
            ])

    # CSV をレスポンスとして返す
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=results.csv"}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)