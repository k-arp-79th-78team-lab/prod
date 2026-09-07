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

### Cloudflare + Render での公開

Flask は Cloudflare Pages では実行できないため、Render をアプリ実行基盤、Cloudflare を DNS と HTTPS プロキシとして使用します。

1. Render の Web Service にこのリポジトリを接続します。
2. 起動コマンドを `gunicorn app:app` に設定します。
3. Render の Custom Domains に `karp-79th-78team.com` を追加し、表示された検証値を Cloudflare DNS に登録します。
4. Cloudflare DNS で `karp-79th-78team.com` を Render の指定先へ CNAME 登録し、プロキシを有効にします。
5. `https://karp-79th-78team.com/health` が `ok` を返すことを確認します。

HTML/JS/API はすべて同じ本番ドメインから提供するため、ログインや回答送信は相対 URL で動作します。Cloudflare 側では `/submit`、`/register-account`、`/admin/*` などの API をキャッシュしない設定にしてください。

Cloudflare の DNS を使わず Render の URL を直接使う場合は、環境変数 `CORS_ORIGINS` に許可する URL をカンマ区切りで指定してください。
