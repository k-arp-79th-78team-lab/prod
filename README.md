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

本番環境では、Flask アプリをそのまま公開して、HTML/JS/API を同じドメインから提供する構成にしてください。これにより、Firebase 認証後の `/register-account` などの API 呼び出しが正常に動きます。

## 環境変数

- `GOOGLE_SHEET_ID`: Google Sheets のスプレッドシート ID
- `SERVICE_ACCOUNT_JSON`: JSON 形式のサービスアカウント認証情報（ローカルに `service_account.json` がない場合）
- `PORT`: アプリを起動するポート（デフォルト 5000）

## デプロイ

Heroku / Render などでは `Procfile` を使用して起動できます。

```bash
gunicorn app:app
```

### Render での公開

1. Render の Web Service にこのリポジトリを接続します。
2. `gunicorn app:app` を起動コマンドとして設定します。
3. 生成された Render URL をブラウザで開き、必要に応じてフロントエンド側で API のベース URL を設定します。

フロントエンドの HTML から Render のバックエンドを使う場合、ページ読み込み前に次のように設定してください。

```html
<script>
  window.__APP_API_BASE_URL__ = 'https://<your-render-service>.onrender.com';
</script>
```

この設定を入れると、ログインや回答送信などの API 呼び出しが Render 側に向きます。
