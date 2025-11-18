# モデル仕様書

## 概要

oricoh_agentで使用するDjangoモデルの詳細仕様です。すべてのモデルはマルチテナント対応のため、`org`（Organization）への外部キーを持ちます。

---

## 1. Organization（組織）

### 説明
テナント（企業）を表すモデル。すべてのデータはこの組織に紐づきます。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | 組織の一意識別子 |
| name | CharField | MaxLength=255, Not Null | 組織名 |
| created_at | DateTimeField | Auto Now Add | 作成日時 |
| updated_at | DateTimeField | Auto Now | 更新日時 |

### インデックス
- `name`（検索用）

### 制約
- `name`は一意である必要がある（同一組織名の重複を防ぐ）

---

## 2. User（ユーザー）

### 説明
システムにログインするユーザーを表すモデル。必ず1つの組織に所属します。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | ユーザーの一意識別子 |
| username | CharField | MaxLength=150, Unique, Not Null | ユーザー名（ログインID） |
| password_hash | CharField | MaxLength=255, Not Null | パスワードハッシュ（bcrypt等） |
| email | EmailField | MaxLength=255, Null=True | メールアドレス |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null | 所属組織 |
| is_active | BooleanField | Default=True | アクティブフラグ |
| created_at | DateTimeField | Auto Now Add | 作成日時 |
| updated_at | DateTimeField | Auto Now | 更新日時 |

### インデックス
- `username`（ログイン検索用）
- `org`（組織フィルタ用）
- `(org, username)`（複合インデックス）

### 制約
- `username`は組織内で一意である必要がある（複合ユニーク制約）

### 関連
- `org`: Organization（多対1）

---

## 3. Document（文書）

### 説明
アップロードまたはMicrosoft365から取り込んだ文書を表すモデル。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | 文書の一意識別子 |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null | 所属組織 |
| filename | CharField | MaxLength=500, Not Null | ファイル名 |
| file_path | CharField | MaxLength=1000, Not Null | ストレージ内のファイルパス |
| file_type | CharField | MaxLength=50, Not Null | ファイルタイプ（pdf/docx/xlsx/pptx/image等） |
| file_size | BigIntegerField | Not Null | ファイルサイズ（バイト） |
| mime_type | CharField | MaxLength=100, Null=True | MIMEタイプ |
| metadata | JSONField | Null=True | メタデータ（ページ数、作成日、作成者等） |
| status | CharField | MaxLength=20, Default='pending' | 処理ステータス（pending/processing/completed/failed） |
| error_message | TextField | Null=True | エラーメッセージ（失敗時） |
| source | CharField | MaxLength=50, Default='upload' | 取り込み元（upload/microsoft365/local_folder） |
| source_id | CharField | MaxLength=255, Null=True | 取り込み元のID（Microsoft365のitem_id等） |
| created_at | DateTimeField | Auto Now Add | 作成日時 |
| updated_at | DateTimeField | Auto Now | 更新日時 |

### インデックス
- `org`（組織フィルタ用）
- `status`（ステータス検索用）
- `source`（取り込み元検索用）
- `(org, status)`（複合インデックス）
- `created_at`（時系列検索用）

### 制約
- `file_type`は許可リストで検証（pdf, docx, xlsx, pptx, jpg, png, gif等）
- `status`は選択肢で検証（pending, processing, completed, failed）

### 関連
- `org`: Organization（多対1）

---

## 4. Chunk（チャンク）

### 説明
文書を意味単位で分割したチャンクを表すモデル。RAG検索の基本単位です。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | チャンクの一意識別子 |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null | 所属組織 |
| document | ForeignKey | To=Document, On Delete=CASCADE, Not Null | 元の文書 |
| chunk_text | TextField | Not Null | チャンクのテキスト内容 |
| chunk_index | IntegerField | Not Null | チャンクの順序（文書内での位置） |
| chunk_type | CharField | MaxLength=50, Default='text' | チャンクタイプ（text/table/image/heading等） |
| page_number | IntegerField | Null=True | ページ番号（PDF等の場合） |
| metadata | JSONField | Null=True | メタデータ（見出しレベル、セクション情報等） |
| created_at | DateTimeField | Auto Now Add | 作成日時 |

### インデックス
- `org`（組織フィルタ用）
- `document`（文書フィルタ用）
- `(document, chunk_index)`（順序検索用）
- `chunk_type`（タイプ検索用）

### 制約
- `chunk_text`は空文字列不可
- `chunk_index`は0以上
- `(document, chunk_index)`は一意（同一文書内で重複不可）

### 関連
- `org`: Organization（多対1）
- `document`: Document（多対1）

---

## 5. Embedding（埋め込みベクトル）

### 説明
チャンクのベクトル表現を表すモデル。RAG検索に使用されます。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | 埋め込みの一意識別子 |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null | 所属組織 |
| chunk | ForeignKey | To=Chunk, On Delete=CASCADE, Not Null, Unique | 対応するチャンク（1対1） |
| vector | TextField | Not Null | ベクトルデータ（JSON配列またはバイナリ） |
| model_name | CharField | MaxLength=100, Default='text-embedding-3-large' | 使用したモデル名 |
| dimension | IntegerField | Default=3072 | ベクトルの次元数 |
| metadata | JSONField | Null=True | メタデータ（生成日時、モデルパラメータ等） |
| created_at | DateTimeField | Auto Now Add | 作成日時 |

### インデックス
- `org`（組織フィルタ用）
- `chunk`（チャンク検索用、ユニーク）
- `model_name`（モデル検索用）

### 制約
- `chunk`は一意（1チャンク=1埋め込み）
- `dimension`は正の整数
- `vector`は有効なベクトル形式である必要がある

### 関連
- `org`: Organization（多対1）
- `chunk`: Chunk（1対1）

### 注意事項
- ベクトルデータはSQLite VectorまたはMilvus/pgvectorに保存される場合がある
- このモデルはメタデータ管理用で、実際のベクトル検索は専用DBで行う

---

## 6. ChatLog（チャットログ）

### 説明
ユーザーとAIの対話履歴を表すモデル。エージェントごとに分離されます。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | ログの一意識別子 |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null | 所属組織 |
| agent | ForeignKey | To=Agent, On Delete=CASCADE, Not Null | 使用したエージェント |
| user | ForeignKey | To=User, On Delete=CASCADE, Not Null | 質問したユーザー |
| question | TextField | Not Null | ユーザーの質問 |
| answer | TextField | Not Null | AIの回答 |
| citations | JSONField | Null=True | 参照元情報（チャンクID、文書ID、スコア等） |
| model_name | CharField | MaxLength=100, Default='gpt-4.1' | 使用したAIモデル名 |
| tokens_used | IntegerField | Null=True | 使用トークン数 |
| response_time_ms | IntegerField | Null=True | 応答時間（ミリ秒） |
| created_at | DateTimeField | Auto Now Add | 作成日時 |

### インデックス
- `org`（組織フィルタ用）
- `agent`（エージェントフィルタ用）
- `user`（ユーザーフィルタ用）
- `created_at`（時系列検索用）
- `(org, agent, created_at)`（複合インデックス）
- `(org, user, created_at)`（複合インデックス）

### 制約
- `question`と`answer`は空文字列不可
- `tokens_used`は0以上
- `response_time_ms`は0以上

### 関連
- `org`: Organization（多対1）
- `agent`: Agent（多対1）
- `user`: User（多対1）

### citationsの構造例
```json
{
  "chunks": [
    {
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "example.pdf",
      "score": 0.95,
      "page_number": 1
    }
  ]
}
```

---

## 7. Agent（AIエージェント）

### 説明
ユーザーが作成するAIエージェントを表すモデル。各エージェントは特定の学習データセット（文書群）を参照し、独立したチャット履歴を持ちます。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | エージェントの一意識別子 |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null | 所属組織 |
| created_by | ForeignKey | To=User, On Delete=SET_NULL, Null=True | 作成者 |
| name | CharField | MaxLength=255, Not Null | エージェント名 |
| description | TextField | Null=True | エージェントの説明 |
| model_name | CharField | MaxLength=100, Default='gpt-4.1' | 使用するAIモデル名 |
| temperature | FloatField | Default=0.7 | 温度パラメータ（0.0-2.0） |
| max_results | IntegerField | Default=5 | ベクトル検索の最大結果数（1-20） |
| system_prompt | TextField | Null=True | システムプロンプト（カスタム指示） |
| is_active | BooleanField | Default=True | アクティブフラグ |
| created_at | DateTimeField | Auto Now Add | 作成日時 |
| updated_at | DateTimeField | Auto Now | 更新日時 |

### インデックス
- `org`（組織フィルタ用）
- `created_by`（作成者フィルタ用）
- `is_active`（アクティブエージェント検索用）
- `(org, is_active)`（複合インデックス）

### 制約
- `name`は組織内で一意である必要がある（複合ユニーク制約）
- `temperature`は0.0から2.0の間
- `max_results`は1から20の間

### 関連
- `org`: Organization（多対1）
- `created_by`: User（多対1）
- `documents`: Document（多対多、AgentDocument経由）

---

## 8. AgentDocument（エージェント-文書関連）

### 説明
エージェントと文書の関連を表す中間テーブル。エージェントが参照する学習データを定義します。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | 関連の一意識別子 |
| agent | ForeignKey | To=Agent, On Delete=CASCADE, Not Null | エージェント |
| document | ForeignKey | To=Document, On Delete=CASCADE, Not Null | 文書 |
| added_at | DateTimeField | Auto Now Add | 追加日時 |

### インデックス
- `agent`（エージェントフィルタ用）
- `document`（文書フィルタ用）
- `(agent, document)`（複合インデックス、ユニーク）

### 制約
- `(agent, document)`は一意（同じ文書を重複追加不可）

### 関連
- `agent`: Agent（多対1）
- `document`: Document（多対1）

---

## 9. Microsoft365Connection（Microsoft365接続情報）

### 説明
組織のMicrosoft365接続情報を保存するモデル（オプション）。

### フィールド

| フィールド名 | 型 | 制約 | 説明 |
|------------|-----|------|------|
| id | UUID | Primary Key, Auto | 接続の一意識別子 |
| org | ForeignKey | To=Organization, On Delete=CASCADE, Not Null, Unique | 所属組織（1組織=1接続） |
| tenant_id | CharField | MaxLength=255, Not Null | Azure ADテナントID |
| client_id | CharField | MaxLength=255, Not Null | アプリケーション（クライアント）ID |
| client_secret_encrypted | CharField | MaxLength=500, Not Null | 暗号化されたクライアントシークレット |
| refresh_token_encrypted | TextField | Null=True | 暗号化されたリフレッシュトークン |
| is_active | BooleanField | Default=True | 接続有効フラグ |
| last_sync_at | DateTimeField | Null=True | 最終同期日時 |
| sync_settings | JSONField | Null=True | 同期設定（対象フォルダ、更新頻度等） |
| created_at | DateTimeField | Auto Now Add | 作成日時 |
| updated_at | DateTimeField | Auto Now | 更新日時 |

### インデックス
- `org`（組織検索用、ユニーク）
- `is_active`（アクティブ接続検索用）

### 制約
- `org`は一意（1組織=1接続）
- 機密情報は暗号化して保存

### 関連
- `org`: Organization（1対1）

---

## マルチテナント設計の原則

### 1. すべてのモデルに`org`フィールドを持つ
- データの完全な分離を保証
- クエリ時は必ず`org`でフィルタ

### 2. QuerySetのフィルタリング
```python
# 必ずorgでフィルタ
Document.objects.filter(org=request.user.org)
```

### 3. ストレージの分離
- ファイルパス: `/storage/{org_id}/{filename}`
- ベクトルDB: メタデータに`org_id`を含める

### 4. JWTトークンに`org_id`を含める
- バックエンドで検証
- 他組織のデータアクセスを防止

---

## マイグレーション戦略

1. 初期マイグレーションで全モデルを作成
2. `org`フィールドは必須（NULL不可）
3. 既存データがある場合は移行スクリプトが必要
4. インデックスは段階的に追加（パフォーマンス考慮）

---

## 変更履歴

| 日付 | 変更内容 | 変更理由 |
|------|---------|---------|
| 2024-XX-XX | 初版作成 | プロジェクト開始 |
| 2024-XX-XX | Agent、AgentDocumentモデル追加、ChatLogにagentフィールド追加、Documentのsourceにlocal_folder追加 | AIエージェント機能とローカルフォルダ対応の追加 |

