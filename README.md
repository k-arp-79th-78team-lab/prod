# prod

K-ARP 79期78班の参加者向け Web クイズアプリケーションです。

## 使い方

1. リポジトリをクローンします。
2. 仮想環境を作成し、依存パッケージをインストールします。

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. アプリを起動します。

```bash
python app.py
```

4. ブラウザで `http://localhost:5000` にアクセスします。

## 環境変数

- `GOOGLE_SHEET_ID`: Google Sheets のスプレッドシート ID
- `SERVICE_ACCOUNT_JSON`: JSON 形式のサービスアカウント認証情報（ローカルに `service_account.json` がない場合）
- `PORT`: アプリを起動するポート（デフォルト 5000）

## デプロイ

Heroku / Render などでは `Procfile` を使用して起動できます。

```bash
gunicorn app:app
```
