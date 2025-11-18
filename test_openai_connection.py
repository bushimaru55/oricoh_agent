#!/usr/bin/env python3
"""
OpenAI API接続テストスクリプト
APIキーの有効性を確認します。
"""

import os
import sys
from openai import OpenAI

def test_openai_connection(api_key: str):
    """OpenAI APIへの接続をテストします"""
    try:
        # OpenAIクライアントを初期化
        client = OpenAI(api_key=api_key)
        
        print("🔍 OpenAI API接続テストを開始します...")
        print("-" * 50)
        
        # 1. モデル一覧の取得テスト（軽量なAPI呼び出し）
        print("\n1. モデル一覧の取得をテスト中...")
        models = client.models.list()
        print(f"   ✅ 成功: {len(list(models.data))}件のモデルを取得")
        
        # 2. 簡単なチャット完了テスト
        print("\n2. チャット完了APIをテスト中...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test. Please respond with 'OK'."}
            ],
            max_tokens=10
        )
        print(f"   ✅ 成功: {response.choices[0].message.content}")
        
        # 3. Embedding APIのテスト
        print("\n3. Embedding APIをテスト中...")
        embedding_response = client.embeddings.create(
            model="text-embedding-3-small",
            input="test"
        )
        embedding_dimension = len(embedding_response.data[0].embedding)
        print(f"   ✅ 成功: ベクトル次元数 = {embedding_dimension}")
        
        print("\n" + "=" * 50)
        print("✅ すべてのテストが成功しました！")
        print("✅ APIキーは有効です。")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 50)
        print("❌ エラーが発生しました:")
        print(f"   {str(e)}")
        print("=" * 50)
        return False

if __name__ == "__main__":
    # APIキーを引数から取得、または環境変数から取得
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ エラー: APIキーが指定されていません")
            print("使用方法:")
            print("  python test_openai_connection.py <API_KEY>")
            print("  または環境変数 OPENAI_API_KEY を設定してください")
            sys.exit(1)
    
    success = test_openai_connection(api_key)
    sys.exit(0 if success else 1)

