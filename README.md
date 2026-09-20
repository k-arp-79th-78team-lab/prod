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

# 実験概要

本プロジェクトは、高校生の当事者視点から**「紙とデジタルの認知特性（脳への負荷）の違い」**を解明し、**「学習効率を最大化するデジタル教材のUI（ユーザーインターフェース）設計指針」**を検証・提案するための研究実験プロジェクトです。

---

## 1. 研究の背景と目的 (Context & Purpose)

GIGAスクール構想により1人1台端末が定着したものの、デジタル教材の活用はPDF閲覧や簡易小テストにとどまっています。本研究では「紙かデジタルか」という二者択一の優劣論争を避け、双方の**「認知特性（認知負荷）」**を科学的に測定・評価した上で、**「デジタルの弱点（認知負荷）を改善する最適UI」**を実証的に検証することを目的としています。

### 研究の問い (Research Questions)
* **RQ1（特性の解明）:** 暗記タスクにおいて、アナログ（紙）とデジタルで学習者の認知負荷（正答数・回答時間・主観的評価）にどのような「特性の違い」が現れるか？
* **RQ2（UI最適化）:** 画面のデザイン操作（フォント、配色、文字サイズ、レイアウト、行間等）を施すことで、デジタル特有の認知負荷を低減し、学習効率（正答数向上・回答時間短縮）を向上させられるか？

---

## 2. 実験設計と変数 (Experimental Design)

* **被験者:** 高校生 60名程度（2群比較：各群30名）
* **タスク:** 造語（20語程度）の暗記および選択式・記述式テスト（5〜10分）

### 【本実験 I：ベースライン測定（紙 vs デジタル）】
* **目的:** 初期状態における紙とデジタルの認知特性・負荷の違いを計測
* **独立変数:** 提示・解答メディア（アナログ群[紙] vs デジタル群[独自Webシステム]）
* **従属変数:**
  * **客観的評価:** テスト正答数、回答時間（ミリ秒単位で計測）
  * **主観的評価:** アンケート（自己評価・見やすさ・疲労度）
* **統制変数:** 問題難易度、実験環境（照明・騒音）、端末スペック/画面サイズ（11インチiPad等）
* **媒介変数:** デジタル機器への慣れ（事前アンケートで可視化）

### 【本実験 II：UI最適化検証（デフォルトUI vs 改善UI）】
* **目的:** 科学的根拠に基づいたデザイン操作による認知負荷低減効果を実証
* **独立変数:** デジタル側のUIデザイン（デフォルトUI群 vs 認知負荷低減UI群）
* **従属変数:** テスト正答数、回答時間（ミリ秒単位）、主観的評価