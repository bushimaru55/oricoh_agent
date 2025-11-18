# oricoh_agent — Microsoft365 × 社内ナレッジAI × マルチモーダル × マルチテナント  
MVP開発向け Cursor 専用 指示書（完全版）

---

# 0. プロジェクト名

oricoh_agent

---

# 1. プロダクト概要

**oricoh_agent** は、企業ごとの社内ナレッジ（Microsoft365 / PDF / Office / 画像）を  
**マルチモーダル解析 → 構造化 → RAG検索 → AI回答**  
まで一体で行う **組織専属AIエージェント** です。

目標：

- Microsoft365（SharePoint / OneDrive）から自動取り込み
- PDF / Office / 画像 / 図表を GPT-4o / o1-preview で高精度解析
- マルチモーダルRAGで高精度な回答生成
- 各組織（テナント）ごとに完全データ分離（セキュリティ最優先）
- Next.js のモダンUI
- MVPでは SQLite Vector、本番で Milvus または pgvector に移行可能
- すべて Docker コンテナで動作

この README は Cursor Composer が参照して自動生成するための **最終指示書** です。

---

# 2. 全体アーキテクチャ

```
oricoh_agent/
├ frontend（Next.js）
├ backend（Django）
├ vector（SQLite Vector）
├ nginx（Reverse Proxy）
├ docker-compose.dev.yml
├ docker-compose.prod.yml
```

### 技術構成

| 層 | 技術 |
|----|------|
| フロント | Next.js 14 + TypeScript + Tailwind |
| API | Django REST Framework |
| DB | SQLite（開発）→ PostgreSQL（本番） |
| Vector DB | SQLite Vector（MVP）→ Milvus（本番） |
| AI | OpenAI（GPT-4.1 / GPT-4o / o1-preview / embedding-3-large） |
| 認証 | JWT（org_id 含む） |
| 取り込み | Microsoft Graph API |
| マルチモーダル | GPT-4o / o1-preview |

---

# 3. Docker コンテナ構成

```
frontend: Next.js
backend: Django（gunicorn/uvicorn）
vector: SQLite Vector（volume）
nginx: Reverse Proxy
db（本番）: PostgreSQL
```

---

# 4. ディレクトリ構成（Cursorが生成するべき構造）

```
oricoh_agent/
AIdocs/
README_MVP.md

backend/
Dockerfile
requirements.txt
config/
__init__.py
settings.py
urls.py
wsgi.py
apps/
auth/
organization/
document/
rag/
chat/
storage/
org_1/
org_2/

frontend/
Dockerfile
package.json
next.config.js
src/
app/
login/
chat/
upload/
documents/

vector/
data/

nginx/
nginx.conf

docker-compose.dev.yml
docker-compose.prod.yml
.env.example
```

---

# 5. Django apps 設計

### **auth**
- JWT認証
- ログイン
- JWTに org_id を含める

### **organization**
- テナント（企業）管理

### **document**
- 文書アップロード
- Microsoft365取り込み
- GPT-4o / o1-preview でマルチモーダル解析
- チャンク作成

### **rag**
- Embedding生成（embedding-3-large）
- SQLite Vector 検索
- 本番は Milvus or pgvector に切り替え可能

### **chat**
- 質問 → ベクトル検索 → AI回答
- 回答と参照元（citations）を保存

---

# 6. マルチテナント安全設計（最重要仕様）

### 全モデルが org_id を持つ  
```
Organization
User
Document
Chunk
Embedding
ChatLog
```

### QuerySetは必ず org_id 絞り込み  
例：  
```python
Chunk.objects.filter(org=request.user.org)
```

### ストレージも組織ごとに分離

```
/storage/org_1/
/storage/org_2/
```

### JWTにorg_idを含めてバックエンドで検証

→ 他組織のデータは絶対に参照不可。

---

# 7. モデル仕様

## Organization

```
id
name
created_at
```

## User

```
id
username
password_hash
org (FK)
```

## Document

```
id
org(FK)
filename
file_path
file_type
metadata(json)
created_at
```

## Chunk

```
id
org(FK)
document(FK)
chunk_text
chunk_index
```

## Embedding

```
id
org(FK)
chunk(FK)
vector
metadata(json)
```

## ChatLog

```
id
org(FK)
user(FK)
question
answer
citations(json)
created_at
```

---

# 8. API 仕様（OpenAPI 風）

### POST /api/auth/login

→ JWT 発行（org_id含む）

### POST /api/document/upload

* ファイル保存
* GPT-4o / o1-preview 解析
* チャンク・Embedding生成
* org_id で紐づけ

### POST /api/chat/query

入力：question
処理：

1. org_id でフィルタ
2. ベクトル検索（SQLite Vector）
3. OpenAI（GPT-4.1）で回答
4. citations を生成して返す

---

# 9. マルチモーダル解析仕様（高精度）

### 使用モデル

* GPT-4o（画像解析／表／図に強い）
* o1-preview（最も高精度な構造化）
* GPT-4.1（文章理解）
* embedding-3-large（RAG向け）

### 手順

1. PDF/Office をサーバーで受け取る
2. 必要に応じてページ画像化
3. o1-preview で構造化抽出（Markdown）
4. 意味単位でチャンクする
5. Embedding生成
6. SQLite Vector に保存

---

# 10. RAGパイプライン

### チャンク分割

* 2000〜2500文字
* H1/H2/H3 単位
* 表 → Markdown

### ベクトル化

* OpenAI embedding-3-large（3072次元）
* org_id / document_id を metadata に保存

### 検索

SQLite Vector（MVP）
本番は Milvus / pgvector に切り替え可能

### 回答生成

GPT-4.1 or o1-mini
citations を返す

---

# 11. Next.js UI仕様

### /login

JWTログイン

### /upload

文書アップロード（PDF / Office / 画像）

### /documents

文書一覧・ステータス

### /chat

RAGチャットUI

* 質問入力
* 回答と citations 表示
* 会話履歴

---

# 12. Dockerfile（backend）

```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

# 13. Dockerfile（frontend）

```dockerfile
FROM node:20
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

---

# 14. docker-compose.dev.yml

```yaml
version: "3"

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./vector:/vector
    env_file:
      - .env

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
```

---

# 15. .env.example

```
SECRET_KEY=changeme
DEBUG=True

OPENAI_API_KEY=sk-xxx

DB_ENGINE=sqlite
VECTOR_DB_PATH=/vector/data/vector.sqlite3
```

---

# 16. 本番対応（Milvus / PostgreSQL）

### 後から以下を追加するだけで移行可能

* db（PostgreSQL）
* vector（Milvus）
* backend の DB 設定を pg に変更
* rag layer で Milvus 接続に切り替え

---

# 17. 今後の拡張

* Teams / Slack エージェント化
* 文書差分同期（Graph Delta API）
* 企画書生成エージェント
* 自動社内業務ワークフロー
* マルチモーダルのリアルタイム解析
* オートメーションエージェント（行動AI）

---

# 🎯 Cursor Composer に対する最終命令

**「この README_MVP.md の仕様に基づいて、`oricoh_agent` プロジェクトを生成してください。」**

