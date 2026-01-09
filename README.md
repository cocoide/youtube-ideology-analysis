# YouTube Comment Collection Tool for Thesis Pilot Study

卒論パイロット用のYouTubeコメント収集ツールです。指定した動画のトップレベルコメントをページネーションで取得し、CSVやSQLiteデータベースに保存します。

## 必要要件

- Python 3.11+
- YouTube Data API v3のAPIキー

## インストール

```bash
pip install -e .
```

または依存関係のみインストール:

```bash
pip install google-api-python-client pytest pytest-mock
```

## 環境設定

YouTube Data API v3のAPIキーを環境変数に設定してください：

```bash
export YOUTUBE_API_KEY='your-api-key-here'
```

## 使用方法

### CLI実行例

```bash
# 基本的な使用例（CSV出力）
python -m yt_pilot --video VBxArHcLEqg --video E190NJcbcys --csv out/comments.csv

# SQLiteデータベースに保存
python -m yt_pilot --video VBxArHcLEqg --db out/comments.sqlite

# 両方の形式で保存（最大200コメント、関連性順）
python -m yt_pilot --video VBxArHcLEqg --max-comments 200 --order relevance --csv out/comments.csv --db out/comments.sqlite
```

### パラメータ

- `--video`: 動画ID（複数指定可）
- `--max-comments`: 動画あたりの最大コメント数（デフォルト: 500）
- `--order`: コメントの並び順 `time` または `relevance`（デフォルト: time）
- `--csv`: CSV出力パス（省略可）
- `--db`: SQLite出力パス（省略可）

※ `--csv` か `--db` のどちらか一つは必須です。

## 出力形式

### CSV形式

以下のカラムを持つCSVファイルが出力されます：

- videoId
- videoPublishedAt
- commentId
- publishedAt
- updatedAt
- likeCount
- totalReplyCount
- text

### SQLiteデータベース

2つのテーブルが作成されます：

**videos テーブル:**
- video_id (TEXT PRIMARY KEY)
- published_at (TEXT)

**comments テーブル:**
- comment_id (TEXT PRIMARY KEY)
- video_id (TEXT)
- video_published_at (TEXT)
- published_at (TEXT)
- updated_at (TEXT)
- like_count (INTEGER)
- total_reply_count (INTEGER)
- text (TEXT)

重複コメントは自動的にスキップされます。

## 出力例

```
Processing video: VBxArHcLEqg
  Fetched: 324 comments
  Saved: 324 new comments
  Skipped: 0 duplicate comments

Processing video: E190NJcbcys
  Fetched: 156 comments
  Saved: 156 new comments
  Skipped: 0 duplicate comments

Total comments collected: 480
CSV saved to: out/comments.csv
Database saved to: out/comments.sqlite
```

## テスト実行

```bash
# すべてのテストを実行
pytest

# 詳細な出力付きで実行
pytest -v

# 特定のテストファイルのみ実行
pytest tests/test_api.py
```

## エラーハンドリング

- 動画が見つからない場合：videoPublishedAtは空文字列になります
- コメントが無効な場合：その動画は0件として処理され、次の動画の処理に進みます
- API制限に達した場合：エラーメッセージが表示されます

## 注意事項

- YouTube Data APIには利用制限があります
- 大量のコメント取得には時間がかかる場合があります
- 再実行時、SQLiteデータベースは既存のコメントをスキップします# youtube-ideology-analysis
