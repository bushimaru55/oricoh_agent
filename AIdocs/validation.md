# バリデーション仕様書

## 概要

oricoh_agentの入力値バリデーション仕様です。フロントエンドとバックエンドの両方で実装します。

---

## バリデーション方針

### 基本原則
- **二重チェック**: フロントエンドとバックエンドの両方でバリデーション
- **ユーザーフレンドリー**: 明確なエラーメッセージ
- **セキュリティ重視**: バックエンドでの厳格な検証
- **パフォーマンス**: 不要な処理を避ける

### バリデーションタイミング
1. **フロントエンド**: ユーザー入力時・送信前
2. **バックエンド**: APIリクエスト受信時

---

## 1. 認証関連バリデーション

### 1.1 ログイン（POST /api/auth/login）

#### ユーザー名（username）
- **必須**: はい
- **型**: 文字列
- **最小長**: 3文字
- **最大長**: 150文字
- **形式**: 
  - メールアドレス形式（`user@example.com`）
  - または英数字・アンダースコア（`user_name`）
- **エラーメッセージ**:
  - 空: "ユーザー名を入力してください"
  - 短すぎる: "ユーザー名は3文字以上で入力してください"
  - 長すぎる: "ユーザー名は150文字以内で入力してください"
  - 形式不正: "ユーザー名の形式が正しくありません"

#### パスワード（password）
- **必須**: はい
- **型**: 文字列
- **最小長**: 8文字
- **最大長**: 128文字
- **形式**: 
  - 英数字・記号を含む（推奨）
  - 空白文字不可
- **エラーメッセージ**:
  - 空: "パスワードを入力してください"
  - 短すぎる: "パスワードは8文字以上で入力してください"
  - 長すぎる: "パスワードは128文字以内で入力してください"
  - 形式不正: "パスワードに空白文字は使用できません"

---

## 2. 文書アップロード関連バリデーション

### 2.1 文書アップロード（POST /api/document/upload）

#### ファイル（file）
- **必須**: はい
- **型**: ファイル（multipart/form-data）
- **対応形式**: 
  - PDF: `.pdf`
  - Word: `.docx`
  - Excel: `.xlsx`
  - PowerPoint: `.pptx`
  - 画像: `.jpg`, `.jpeg`, `.png`, `.gif`
- **最大サイズ**: 100MB（104,857,600バイト）
- **MIMEタイプチェック**: 
  - `application/pdf`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  - `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
  - `application/vnd.openxmlformats-officedocument.presentationml.presentation`
  - `image/jpeg`, `image/png`, `image/gif`
- **エラーメッセージ**:
  - 空: "ファイルを選択してください"
  - 形式不正: "対応していないファイル形式です。PDF、Office、画像ファイルを選択してください"
  - サイズ超過: "ファイルサイズは100MB以下にしてください"
  - MIMEタイプ不一致: "ファイル形式が正しくありません"

#### ソース（source）
- **必須**: いいえ（デフォルト: "upload"）
- **型**: 文字列
- **許可値**: `"upload"`, `"microsoft365"`
- **エラーメッセージ**:
  - 不正な値: "ソースは'upload'または'microsoft365'である必要があります"

---

## 3. チャット関連バリデーション

### 3.1 チャットクエリ（POST /api/chat/query）

#### 質問（question）
- **必須**: はい
- **型**: 文字列
- **最小長**: 1文字（空白のみは不可）
- **最大長**: 2000文字
- **空白文字**: 
  - 先頭・末尾の空白はトリム
  - 連続する空白は1つに正規化（オプション）
- **エラーメッセージ**:
  - 空: "質問を入力してください"
  - 長すぎる: "質問は2000文字以内で入力してください"
  - 空白のみ: "有効な質問を入力してください"

#### モデル（model）
- **必須**: いいえ（デフォルト: "gpt-4.1"）
- **型**: 文字列
- **許可値**: `"gpt-4.1"`, `"o1-mini"`, `"gpt-4o"`
- **エラーメッセージ**:
  - 不正な値: "モデルは'gpt-4.1'、'o1-mini'、'gpt-4o'のいずれかである必要があります"

#### 最大結果数（max_results）
- **必須**: いいえ（デフォルト: 5）
- **型**: 整数
- **最小値**: 1
- **最大値**: 20
- **エラーメッセージ**:
  - 範囲外: "最大結果数は1から20の間で指定してください"

#### 温度（temperature）
- **必須**: いいえ（デフォルト: 0.7）
- **型**: 浮動小数点数
- **最小値**: 0.0
- **最大値**: 2.0
- **エラーメッセージ**:
  - 範囲外: "温度は0.0から2.0の間で指定してください"

---

## 4. Microsoft365同期関連バリデーション

### 4.1 Microsoft365同期（POST /api/document/microsoft365/sync）

#### フォルダパス（folder_path）
- **必須**: はい
- **型**: 文字列
- **最小長**: 1文字
- **最大長**: 500文字
- **形式**: 
  - SharePointサイトパス: `/sites/{site-name}/drive/root:/{folder-path}:`
  - OneDriveパス: `/me/drive/root:/{folder-path}:`
- **エラーメッセージ**:
  - 空: "フォルダパスを入力してください"
  - 長すぎる: "フォルダパスは500文字以内で入力してください"
  - 形式不正: "フォルダパスの形式が正しくありません"

#### 再帰的（recursive）
- **必須**: いいえ（デフォルト: false）
- **型**: ブール値
- **エラーメッセージ**:
  - 型不正: "再帰的は真偽値である必要があります"

---

## 5. 文書一覧取得関連バリデーション

### 5.1 文書一覧（GET /api/document/list）

#### ページ（page）
- **必須**: いいえ（デフォルト: 1）
- **型**: 整数
- **最小値**: 1
- **エラーメッセージ**:
  - 範囲外: "ページ番号は1以上である必要があります"

#### ページサイズ（page_size）
- **必須**: いいえ（デフォルト: 20）
- **型**: 整数
- **最小値**: 1
- **最大値**: 100
- **エラーメッセージ**:
  - 範囲外: "ページサイズは1から100の間で指定してください"

#### ステータス（status）
- **必須**: いいえ
- **型**: 文字列
- **許可値**: `"pending"`, `"processing"`, `"completed"`, `"failed"`
- **エラーメッセージ**:
  - 不正な値: "ステータスは'pending'、'processing'、'completed'、'failed'のいずれかである必要があります"

#### ファイルタイプ（file_type）
- **必須**: いいえ
- **型**: 文字列
- **許可値**: `"pdf"`, `"docx"`, `"xlsx"`, `"pptx"`, `"image"`
- **エラーメッセージ**:
  - 不正な値: "ファイルタイプが正しくありません"

#### 検索（search）
- **必須**: いいえ
- **型**: 文字列
- **最大長**: 100文字
- **エラーメッセージ**:
  - 長すぎる: "検索文字列は100文字以内で入力してください"

---

## 6. チャット履歴関連バリデーション

### 6.1 チャット履歴一覧（GET /api/chat/history）

#### ページ（page）
- **必須**: いいえ（デフォルト: 1）
- **型**: 整数
- **最小値**: 1
- **エラーメッセージ**: 文書一覧と同様

#### ページサイズ（page_size）
- **必須**: いいえ（デフォルト: 20）
- **型**: 整数
- **最小値**: 1
- **最大値**: 100
- **エラーメッセージ**: 文書一覧と同様

#### 開始日時（start_date）
- **必須**: いいえ
- **型**: 日時文字列（ISO 8601形式）
- **形式**: `YYYY-MM-DDTHH:mm:ssZ` または `YYYY-MM-DD`
- **エラーメッセージ**:
  - 形式不正: "開始日時の形式が正しくありません（ISO 8601形式）"

#### 終了日時（end_date）
- **必須**: いいえ
- **型**: 日時文字列（ISO 8601形式）
- **形式**: `YYYY-MM-DDTHH:mm:ssZ` または `YYYY-MM-DD`
- **制約**: `start_date`より後である必要がある
- **エラーメッセージ**:
  - 形式不正: "終了日時の形式が正しくありません（ISO 8601形式）"
  - 範囲不正: "終了日時は開始日時より後である必要があります"

---

## 7. 設定関連バリデーション

### 7.1 パスワード変更（将来の拡張）

#### 現在のパスワード（current_password）
- **必須**: はい
- **型**: 文字列
- **最小長**: 8文字
- **最大長**: 128文字
- **エラーメッセージ**: ログインのパスワードと同様

#### 新しいパスワード（new_password）
- **必須**: はい
- **型**: 文字列
- **最小長**: 8文字
- **最大長**: 128文字
- **制約**: 現在のパスワードと異なる必要がある
- **エラーメッセージ**:
  - 現在と同じ: "新しいパスワードは現在のパスワードと異なる必要があります"
  - その他: ログインのパスワードと同様

#### 確認用パスワード（confirm_password）
- **必須**: はい
- **型**: 文字列
- **制約**: 新しいパスワードと一致する必要がある
- **エラーメッセージ**:
  - 不一致: "パスワードが一致しません"

---

## 8. 実装例

### Django Serializerでの実装例

```python
from rest_framework import serializers
import re

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        min_length=3,
        max_length=150,
        required=True
    )
    password = serializers.CharField(
        min_length=8,
        max_length=128,
        required=True,
        write_only=True
    )
    
    def validate_username(self, value):
        # メールアドレス形式または英数字・アンダースコア
        if not re.match(r'^[\w@.]+$', value):
            raise serializers.ValidationError(
                "ユーザー名の形式が正しくありません"
            )
        return value
    
    def validate_password(self, value):
        if ' ' in value:
            raise serializers.ValidationError(
                "パスワードに空白文字は使用できません"
            )
        return value

class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    source = serializers.ChoiceField(
        choices=['upload', 'microsoft365'],
        default='upload',
        required=False
    )
    
    ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.xlsx', '.pptx', 
                          '.jpg', '.jpeg', '.png', '.gif']
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    
    def validate_file(self, value):
        # ファイル拡張子チェック
        ext = value.name.lower().split('.')[-1]
        if f'.{ext}' not in self.ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                "対応していないファイル形式です"
            )
        
        # ファイルサイズチェック
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                "ファイルサイズは100MB以下にしてください"
            )
        
        return value

class ChatQuerySerializer(serializers.Serializer):
    question = serializers.CharField(
        min_length=1,
        max_length=2000,
        required=True,
        trim_whitespace=True
    )
    model = serializers.ChoiceField(
        choices=['gpt-4.1', 'o1-mini', 'gpt-4o'],
        default='gpt-4.1',
        required=False
    )
    max_results = serializers.IntegerField(
        min_value=1,
        max_value=20,
        default=5,
        required=False
    )
    temperature = serializers.FloatField(
        min_value=0.0,
        max_value=2.0,
        default=0.7,
        required=False
    )
    
    def validate_question(self, value):
        # 空白のみチェック
        if not value.strip():
            raise serializers.ValidationError(
                "有効な質問を入力してください"
            )
        return value.strip()
```

### フロントエンド（React/Next.js）での実装例

```typescript
import { z } from 'zod';

// ログインバリデーションスキーマ
export const loginSchema = z.object({
  username: z
    .string()
    .min(3, 'ユーザー名は3文字以上で入力してください')
    .max(150, 'ユーザー名は150文字以内で入力してください')
    .regex(/^[\w@.]+$/, 'ユーザー名の形式が正しくありません'),
  password: z
    .string()
    .min(8, 'パスワードは8文字以上で入力してください')
    .max(128, 'パスワードは128文字以内で入力してください')
    .refine((val) => !val.includes(' '), {
      message: 'パスワードに空白文字は使用できません',
    }),
});

// チャットクエリバリデーションスキーマ
export const chatQuerySchema = z.object({
  question: z
    .string()
    .min(1, '質問を入力してください')
    .max(2000, '質問は2000文字以内で入力してください')
    .refine((val) => val.trim().length > 0, {
      message: '有効な質問を入力してください',
    }),
  model: z.enum(['gpt-4.1', 'o1-mini', 'gpt-4o']).default('gpt-4.1'),
  max_results: z.number().int().min(1).max(20).default(5),
  temperature: z.number().min(0.0).max(2.0).default(0.7),
});

// ファイルアップロードバリデーション
export const validateFile = (file: File): string | null => {
  const allowedExtensions = ['.pdf', '.docx', '.xlsx', '.pptx', 
                            '.jpg', '.jpeg', '.png', '.gif'];
  const maxSize = 100 * 1024 * 1024; // 100MB
  
  const ext = '.' + file.name.toLowerCase().split('.').pop();
  if (!allowedExtensions.includes(ext)) {
    return '対応していないファイル形式です';
  }
  
  if (file.size > maxSize) {
    return 'ファイルサイズは100MB以下にしてください';
  }
  
  return null;
};
```

---

## 9. エラーレスポンス形式

### バリデーションエラー時のレスポンス

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "バリデーションエラーが発生しました",
    "details": {
      "username": ["ユーザー名を入力してください"],
      "password": ["パスワードは8文字以上で入力してください"]
    }
  }
}
```

### HTTPステータスコード
- `400 Bad Request`: バリデーションエラー

---

## 10. セキュリティ考慮事項

### ファイルアップロード
- **ファイル名のサニタイズ**: 危険な文字を除去
- **MIMEタイプの検証**: 拡張子だけでなくMIMEタイプも確認
- **ウイルススキャン**: 本番環境ではウイルススキャンを推奨

### SQLインジェクション対策
- **ORM使用**: Django ORMを使用（自動エスケープ）
- **生SQL使用時**: パラメータ化クエリを使用

### XSS対策
- **入力値のサニタイズ**: HTMLタグをエスケープ
- **マークダウン表示**: 安全なマークダウンライブラリを使用

---

## 変更履歴

| 日付 | 変更内容 | 変更理由 |
|------|---------|---------|
| 2024-XX-XX | 初版作成 | プロジェクト開始 |

