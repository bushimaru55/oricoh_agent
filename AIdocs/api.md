# API仕様書

## 概要

oricoh_agentのRESTful API仕様書です。すべてのAPIはマルチテナント対応で、JWT認証が必要です。

---

## 認証方式

### JWT（JSON Web Token）
- すべてのAPI（`/api/auth/login`を除く）はJWT認証が必要
- JWTペイロードに`org_id`を含める
- ヘッダー形式: `Authorization: Bearer <token>`

### JWTペイロード構造
```json
{
  "user_id": "uuid",
  "org_id": "uuid",
  "username": "string",
  "exp": 1234567890
}
```

---

## エラーレスポンス形式

### 標準エラーレスポンス
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": {}
  }
}
```

### HTTPステータスコード
- `200`: 成功
- `201`: 作成成功
- `400`: バリデーションエラー
- `401`: 認証エラー
- `403`: 権限エラー
- `404`: リソース不存在
- `500`: サーバーエラー

---

## 1. 認証API

### 1.1 POST /api/auth/login

ユーザーログインを行い、JWTトークンを発行します。

#### リクエスト
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

#### レスポンス（成功）
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid",
    "username": "user@example.com",
    "org_id": "uuid",
    "org_name": "組織名"
  }
}
```

#### レスポンス（失敗）
```json
{
  "error": {
    "code": "AUTH_FAILED",
    "message": "ユーザー名またはパスワードが正しくありません"
  }
}
```

#### ステータスコード
- `200`: 成功
- `401`: 認証失敗

---

### 1.2 POST /api/auth/refresh

JWTトークンをリフレッシュします。

#### リクエストヘッダー
```
Authorization: Bearer <token>
```

#### レスポンス（成功）
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### ステータスコード
- `200`: 成功
- `401`: トークン無効

---

## 2. 文書管理API

### 2.1 POST /api/document/upload

文書をアップロードし、マルチモーダル解析・チャンク分割・Embedding生成を行います。

#### リクエスト
- Content-Type: `multipart/form-data`
- 認証: 必須

#### リクエストボディ
```
file: <ファイル>
source: "upload" (オプション、デフォルト: "upload")
```

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "filename": "example.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "status": "processing",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 処理フロー
1. ファイルを保存（`/storage/{org_id}/{filename}`）
2. Documentレコード作成（status: "processing"）
3. バックグラウンドで以下を実行:
   - GPT-4o/o1-previewでマルチモーダル解析
   - チャンク分割（2000-2500文字、H1/H2/H3単位）
   - Embedding生成（embedding-3-large）
   - SQLite Vectorに保存
   - Document.statusを"completed"に更新

#### ステータスコード
- `201`: アップロード成功（処理開始）
- `400`: バリデーションエラー（ファイル形式不正等）
- `413`: ファイルサイズ超過

#### 対応ファイル形式
- PDF: `.pdf`
- Office: `.docx`, `.xlsx`, `.pptx`
- 画像: `.jpg`, `.jpeg`, `.png`, `.gif`

---

### 2.2 GET /api/document/list

組織の文書一覧を取得します。

#### リクエスト
- 認証: 必須
- Query Parameters:
  - `page`: ページ番号（デフォルト: 1）
  - `page_size`: 1ページあたりの件数（デフォルト: 20、最大: 100）
  - `status`: ステータスフィルタ（pending/processing/completed/failed）
  - `file_type`: ファイルタイプフィルタ
  - `search`: ファイル名検索

#### レスポンス（成功）
```json
{
  "count": 100,
  "next": "http://api.example.com/api/document/list?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "filename": "example.pdf",
      "file_type": "pdf",
      "file_size": 1024000,
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:01:00Z"
    }
  ]
}
```

#### ステータスコード
- `200`: 成功

---

### 2.3 GET /api/document/{id}

文書の詳細情報を取得します。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: 文書ID（UUID）

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "filename": "example.pdf",
  "file_type": "pdf",
  "file_size": 1024000,
  "status": "completed",
  "metadata": {
    "page_count": 10,
    "created_date": "2024-01-01"
  },
  "chunk_count": 25,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:01:00Z"
}
```

#### ステータスコード
- `200`: 成功
- `404`: 文書不存在または他組織の文書

---

### 2.4 DELETE /api/document/{id}

文書を削除します（関連するチャンク・Embeddingも削除）。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: 文書ID（UUID）

#### レスポンス（成功）
```json
{
  "message": "文書が削除されました"
}
```

#### ステータスコード
- `200`: 削除成功
- `404`: 文書不存在または他組織の文書

---

### 2.5 POST /api/document/microsoft365/sync

Microsoft365から文書を同期します。

#### リクエスト
- 認証: 必須
- リクエストボディ:
```json
{
  "folder_path": "/sites/sitename/shared documents",
  "recursive": true
}
```

#### レスポンス（成功）
```json
{
  "message": "同期を開始しました",
  "sync_id": "uuid"
}
```

#### 処理フロー
1. Microsoft Graph APIで指定フォルダのファイル一覧取得
2. 新規・更新ファイルを検出
3. 各ファイルを`/api/document/upload`と同様に処理

#### ステータスコード
- `202`: 同期開始
- `400`: 設定エラー
- `503`: Microsoft365接続エラー

---

### 2.6 POST /api/document/local-folder/import

システム内のローカルフォルダから文書を一括取り込みします。

#### リクエスト
- 認証: 必須
- リクエストボディ:
```json
{
  "folder_path": "/data/knowledge_base",
  "recursive": true,
  "file_patterns": ["*.pdf", "*.docx", "*.txt"]
}
```

#### リクエストパラメータ
- `folder_path` (必須): システム内のフォルダパス（絶対パス）
- `recursive` (オプション): 再帰的にサブフォルダも取り込む（デフォルト: false）
- `file_patterns` (オプション): 取り込むファイルパターン（デフォルト: すべての対応形式）

#### レスポンス（成功）
```json
{
  "message": "取り込みを開始しました",
  "import_id": "uuid",
  "files_found": 25,
  "files_queued": 25
}
```

#### 処理フロー
1. 指定フォルダパスが存在し、読み取り可能であることを確認
2. フォルダ内のファイルをスキャン（`recursive`がtrueの場合は再帰的に）
3. `file_patterns`でフィルタ（指定がない場合はすべての対応形式）
4. 各ファイルを`/api/document/upload`と同様に処理
5. `source`: "local_folder"、`source_id`: ファイルパスを設定

#### ステータスコード
- `202`: 取り込み開始
- `400`: バリデーションエラー（フォルダ不存在、パス不正等）
- `403`: フォルダへのアクセス権限なし

---

## 3. エージェント管理API

### 3.1 POST /api/agent/create

新しいAIエージェントを作成します。

#### リクエスト
- 認証: 必須
- リクエストボディ:
```json
{
  "name": "プロジェクト支援エージェント",
  "description": "プロジェクト関連の文書を学習したエージェント",
  "model_name": "gpt-4.1",
  "temperature": 0.7,
  "max_results": 5,
  "system_prompt": "あなたはプロジェクト管理の専門家です。"
}
```

#### リクエストパラメータ
- `name` (必須): エージェント名
- `description` (オプション): エージェントの説明
- `model_name` (オプション): 使用するAIモデル（デフォルト: "gpt-4.1"）
- `temperature` (オプション): 温度パラメータ（デフォルト: 0.7）
- `max_results` (オプション): ベクトル検索の最大結果数（デフォルト: 5）
- `system_prompt` (オプション): システムプロンプト

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "name": "プロジェクト支援エージェント",
  "description": "プロジェクト関連の文書を学習したエージェント",
  "model_name": "gpt-4.1",
  "temperature": 0.7,
  "max_results": 5,
  "system_prompt": "あなたはプロジェクト管理の専門家です。",
  "document_count": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### ステータスコード
- `201`: 作成成功
- `400`: バリデーションエラー
- `409`: 同名のエージェントが既に存在

---

### 3.2 GET /api/agent/list

組織内のエージェント一覧を取得します。

#### リクエスト
- 認証: 必須
- Query Parameters:
  - `page`: ページ番号（デフォルト: 1）
  - `page_size`: 1ページあたりの件数（デフォルト: 20）
  - `is_active`: アクティブフラグでフィルタ（true/false）

#### レスポンス（成功）
```json
{
  "count": 10,
  "next": "http://api.example.com/api/agent/list?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "name": "プロジェクト支援エージェント",
      "description": "プロジェクト関連の文書を学習したエージェント",
      "model_name": "gpt-4.1",
      "document_count": 15,
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### ステータスコード
- `200`: 成功

---

### 3.3 GET /api/agent/{id}

エージェントの詳細情報を取得します。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: エージェントID（UUID）

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "name": "プロジェクト支援エージェント",
  "description": "プロジェクト関連の文書を学習したエージェント",
  "model_name": "gpt-4.1",
  "temperature": 0.7,
  "max_results": 5,
  "system_prompt": "あなたはプロジェクト管理の専門家です。",
  "is_active": true,
  "document_count": 15,
  "documents": [
    {
      "id": "uuid",
      "filename": "project_plan.pdf",
      "file_type": "pdf",
      "added_at": "2024-01-01T00:00:00Z"
    }
  ],
  "created_by": {
    "id": "uuid",
    "username": "user@example.com"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:01:00Z"
}
```

#### ステータスコード
- `200`: 成功
- `404`: エージェント不存在または他組織のエージェント

---

### 3.4 PUT /api/agent/{id}

エージェントの設定を更新します。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: エージェントID（UUID）
- リクエストボディ:
```json
{
  "name": "更新されたエージェント名",
  "description": "更新された説明",
  "model_name": "o1-mini",
  "temperature": 0.8,
  "max_results": 10,
  "system_prompt": "更新されたシステムプロンプト",
  "is_active": true
}
```

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "name": "更新されたエージェント名",
  "description": "更新された説明",
  "model_name": "o1-mini",
  "temperature": 0.8,
  "max_results": 10,
  "system_prompt": "更新されたシステムプロンプト",
  "is_active": true,
  "updated_at": "2024-01-01T00:02:00Z"
}
```

#### ステータスコード
- `200`: 更新成功
- `400`: バリデーションエラー
- `404`: エージェント不存在または他組織のエージェント
- `409`: 同名のエージェントが既に存在

---

### 3.5 DELETE /api/agent/{id}

エージェントを削除します（関連するAgentDocumentも削除、ChatLogは保持）。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: エージェントID（UUID）

#### レスポンス（成功）
```json
{
  "message": "エージェントが削除されました"
}
```

#### ステータスコード
- `200`: 削除成功
- `404`: エージェント不存在または他組織のエージェント

---

### 3.6 POST /api/agent/{id}/documents

エージェントに文書を追加します。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: エージェントID（UUID）
- リクエストボディ:
```json
{
  "document_ids": ["uuid1", "uuid2", "uuid3"]
}
```

#### レスポンス（成功）
```json
{
  "message": "3件の文書が追加されました",
  "added_count": 3,
  "skipped_count": 0
}
```

#### ステータスコード
- `200`: 追加成功
- `400`: バリデーションエラー
- `404`: エージェント不存在または他組織のエージェント

---

### 3.7 DELETE /api/agent/{id}/documents/{document_id}

エージェントから文書を削除します。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: エージェントID（UUID）
  - `document_id`: 文書ID（UUID）

#### レスポンス（成功）
```json
{
  "message": "文書がエージェントから削除されました"
}
```

#### ステータスコード
- `200`: 削除成功
- `404`: エージェントまたは文書不存在、または他組織のリソース

---

## 4. チャットAPI

### 4.1 POST /api/chat/query

RAG検索を実行し、AI回答を生成します。

#### リクエスト
- 認証: 必須
- リクエストボディ:
```json
{
  "agent_id": "uuid",
  "question": "プロジェクトの進捗状況を教えてください"
}
```

#### リクエストパラメータ
- `agent_id` (必須): 使用するエージェントID
- `question` (必須): ユーザーの質問
- `model` (オプション): 使用するAIモデル（エージェント設定を上書き、デフォルト: エージェント設定値）
- `max_results` (オプション): 検索結果の最大数（エージェント設定を上書き、デフォルト: エージェント設定値）
- `temperature` (オプション): 温度パラメータ（エージェント設定を上書き、デフォルト: エージェント設定値）

#### レスポンス（成功）
```json
{
  "answer": "プロジェクトは現在、設計フェーズを完了し、開発フェーズに入っています...",
  "citations": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "プロジェクト計画書.pdf",
      "chunk_text": "プロジェクトは2024年1月に開始され...",
      "score": 0.95,
      "page_number": 1
    }
  ],
  "model_used": "gpt-4.1",
  "tokens_used": 1500,
  "response_time_ms": 1200
}
```

#### 処理フロー
1. JWTから`org_id`を取得
2. エージェントを取得し、`org_id`と`agent_id`で検証
3. エージェントに紐づく文書のチャンクのみを検索対象とする
4. 質問文を`embedding-3-large`でベクトル化
5. SQLite Vectorで類似チャンクを検索（`org_id`とエージェントの文書でフィルタ）
6. 上位N件のチャンクを取得（エージェントの`max_results`設定を使用）
7. エージェントの`model_name`と`temperature`設定を使用して回答生成
8. エージェントの`system_prompt`がある場合はプロンプトに追加
9. ChatLogに保存（`agent_id`を含める）
10. 回答とcitationsを返す

#### ステータスコード
- `200`: 成功
- `400`: バリデーションエラー
- `503`: AIサービスエラー

---

### 4.2 GET /api/chat/history

チャット履歴を取得します。

#### リクエスト
- 認証: 必須
- Query Parameters:
  - `agent_id` (オプション): エージェントIDでフィルタ
  - `page`: ページ番号（デフォルト: 1）
  - `page_size`: 1ページあたりの件数（デフォルト: 20）
  - `start_date`: 開始日時（ISO 8601形式）
  - `end_date`: 終了日時（ISO 8601形式）

#### レスポンス（成功）
```json
{
  "count": 50,
  "next": "http://api.example.com/api/chat/history?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "question": "プロジェクトの進捗状況を教えてください",
      "answer": "プロジェクトは現在...",
      "created_at": "2024-01-01T00:00:00Z",
      "citations_count": 3
    }
  ]
}
```

#### ステータスコード
- `200`: 成功

---

### 4.3 GET /api/chat/history/{id}

特定のチャット履歴の詳細を取得します。

#### リクエスト
- 認証: 必須
- Path Parameters:
  - `id`: チャットログID（UUID）

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "question": "プロジェクトの進捗状況を教えてください",
  "answer": "プロジェクトは現在...",
  "citations": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "プロジェクト計画書.pdf",
      "chunk_text": "プロジェクトは2024年1月に開始され...",
      "score": 0.95,
      "page_number": 1
    }
  ],
  "model_used": "gpt-4.1",
  "tokens_used": 1500,
  "response_time_ms": 1200,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### ステータスコード
- `200`: 成功
- `404`: 履歴不存在または他組織の履歴

---

## 5. 組織管理API

### 5.1 GET /api/organization/info

現在の組織情報を取得します。

#### リクエスト
- 認証: 必須

#### レスポンス（成功）
```json
{
  "id": "uuid",
  "name": "組織名",
  "created_at": "2024-01-01T00:00:00Z",
  "document_count": 100,
  "user_count": 10
}
```

#### ステータスコード
- `200`: 成功

---

## 6. ヘルスチェックAPI

### 6.1 GET /api/health

APIサーバーのヘルスチェックを行います。

#### リクエスト
- 認証: 不要

#### レスポンス（成功）
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### ステータスコード
- `200`: 正常
- `503`: サービス異常

---

## レート制限

### 制限値
- `/api/chat/query`: 1分あたり10リクエスト
- `/api/document/upload`: 1分あたり5リクエスト
- その他: 1分あたり100リクエスト

### レート制限超過時のレスポンス
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "レート制限を超過しました",
    "retry_after": 60
  }
}
```

ステータスコード: `429`

---

## バージョニング

- 現在のバージョン: `v1`
- URLパスにバージョンを含める: `/api/v1/...`
- 将来のバージョンアップ時は後方互換性を維持

---

## 変更履歴

| 日付 | 変更内容 | 変更理由 |
|------|---------|---------|
| 2024-XX-XX | 初版作成 | プロジェクト開始 |
| 2024-XX-XX | エージェント管理API追加、ローカルフォルダ取り込みAPI追加、チャットAPIにagent_id追加 | AIエージェント機能とローカルフォルダ対応の追加 |

