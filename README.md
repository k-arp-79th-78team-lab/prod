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
- `FIREBASE_SERVICE_ACCOUNT_JSON`: Firebase Admin SDK 用サービスアカウントJSON。`SERVICE_ACCOUNT_JSON` と同じFirebaseプロジェクトのサービスアカウントを利用する場合は省略できます
- `PORT`: アプリを起動するポート（デフォルト 5000）

管理者ページは `/admin` で開き、Firebase Authの `admin: true` カスタムクレームを持つアカウントだけが操作できます。Render側で管理者メール一覧を設定する必要はありません。

Firebaseコンソールにはカスタムクレームを直接編集する画面がないため、Firebase Admin SDKで管理者を指定します。取得したユーザーUIDを使い、FirebaseサービスアカウントJSONを用意したうえで、次のコマンドを実行してください。

```bash
python3 set_admin_claim.py 'FirebaseのユーザーUID'
```

サービスアカウントJSONを別の場所に保存している場合は、パスを指定できます。

```bash
python3 set_admin_claim.py 'FirebaseのユーザーUID' --service-account '/path/to/firebase-service-account.json'
```

または、`FIREBASE_SERVICE_ACCOUNT_JSON` / `SERVICE_ACCOUNT_JSON` 環境変数にサービスアカウントJSON全体を設定してください。サービスアカウントJSONはGitにコミットしないでください。権限を外す場合は次のコマンドを実行します。

```bash
python3 set_admin_claim.py 'FirebaseのユーザーUID' --revoke
```

変更後は管理者が一度ログアウトして再ログインし、更新されたIDトークンを取得してください。FirebaseのWebログイン設定では、利用する本番ドメインを承認済みドメインにも追加してください。

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
