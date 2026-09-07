import argparse
import json
import os

import firebase_admin
from firebase_admin import auth, credentials


def initialize_firebase(service_account_path=None):
    service_account_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON') or os.environ.get('SERVICE_ACCOUNT_JSON')
    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError as error:
            raise RuntimeError('サービスアカウントJSONの形式が正しくありません。') from error
        return firebase_admin.initialize_app(credentials.Certificate(service_account_info))

    credential_path = service_account_path or 'firebase-service-account.json'
    if os.path.exists(credential_path):
        return firebase_admin.initialize_app(credentials.Certificate(credential_path))

    raise RuntimeError(
        f'サービスアカウントJSONが見つかりません: {credential_path}\n'
        'FIREBASE_SERVICE_ACCOUNT_JSONを設定するか、--service-accountでJSONファイルを指定してください。'
    )


def main():
    parser = argparse.ArgumentParser(description='Firebaseユーザーの管理者権限を設定します。')
    parser.add_argument('uid', help='Firebase AuthenticationのユーザーUID')
    parser.add_argument('--service-account', help='Firebase Admin SDK用サービスアカウントJSONのパス')
    parser.add_argument('--revoke', action='store_true', help='管理者権限を削除します')
    args = parser.parse_args()

    initialize_firebase(args.service_account)
    user = auth.get_user(args.uid)
    claims = dict(user.custom_claims or {})

    if args.revoke:
        claims.pop('admin', None)
    else:
        claims['admin'] = True

    auth.set_custom_user_claims(args.uid, claims)
    action = '削除' if args.revoke else '付与'
    print(f'{user.email or args.uid} に管理者権限を{action}しました。')
    print('反映には対象ユーザーのログアウトと再ログインが必要です。')


if __name__ == '__main__':
    main()
