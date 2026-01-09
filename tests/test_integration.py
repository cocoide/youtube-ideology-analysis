import pytest
import os
import tempfile
import sqlite3
import csv
from pathlib import Path
from dotenv import load_dotenv
from yt_pilot.api import YouTubeDataFetcher
from yt_pilot.storage import CSVStorage, SQLiteStorage

load_dotenv()


@pytest.mark.skipif(not os.environ.get('YOUTUBE_API_KEY'), reason="No API key provided")
class TestIntegration:
    def test_real_api_fetch_comments(self):
        """実際のAPIを使用してコメントを取得するテスト"""
        api_key = os.environ.get('YOUTUBE_API_KEY')
        fetcher = YouTubeDataFetcher(api_key)
        
        # 短い動画でテスト（コメントが少ない）
        video_id = 'dQw4w9WgXcQ'  # Rick Astley - Never Gonna Give You Up
        comments = fetcher.fetch_comments(video_id, max_comments=10)
        
        assert len(comments) > 0
        assert len(comments) <= 10
        
        # 必須フィールドの確認
        for comment in comments:
            assert comment['videoId'] == video_id
            assert comment['commentId']
            assert comment['text']
            assert 'publishedAt' in comment
            assert 'likeCount' in comment
            assert isinstance(comment['likeCount'], int)
            assert isinstance(comment['totalReplyCount'], int)
    
    def test_real_api_video_info(self):
        """実際のAPIを使用して動画情報を取得するテスト"""
        api_key = os.environ.get('YOUTUBE_API_KEY')
        fetcher = YouTubeDataFetcher(api_key)
        
        video_id = 'dQw4w9WgXcQ'
        video_info = fetcher.get_video_info(video_id)
        
        assert video_info['video_id'] == video_id
        assert video_info['published_at']  # Should not be empty
        assert 'T' in video_info['published_at']  # ISO format check
    
    def test_real_api_with_storage(self):
        """実際のAPIを使用してデータを取得し、ストレージに保存するテスト"""
        api_key = os.environ.get('YOUTUBE_API_KEY')
        fetcher = YouTubeDataFetcher(api_key)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / 'comments.csv'
            db_path = Path(tmpdir) / 'comments.db'
            
            # データ取得
            video_id = 'dQw4w9WgXcQ'
            video_info = fetcher.get_video_info(video_id)
            comments = fetcher.fetch_comments(video_id, max_comments=5)
            
            # videoPublishedAtを設定
            for comment in comments:
                comment['videoPublishedAt'] = video_info['published_at']
            
            # CSV保存
            csv_storage = CSVStorage(str(csv_path))
            csv_storage.save_comments(comments)
            
            assert csv_path.exists()
            
            # CSVの内容確認
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == len(comments)
            
            # SQLite保存
            db_storage = SQLiteStorage(str(db_path))
            db_storage.save_comments(comments)
            
            assert db_path.exists()
            
            # データベースの内容確認
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM comments")
            count = cursor.fetchone()[0]
            assert count == len(comments)
            
            cursor.execute("SELECT COUNT(*) FROM videos")
            video_count = cursor.fetchone()[0]
            assert video_count == 1
            
            conn.close()
    
    def test_pagination_with_real_api(self):
        """実際のAPIでページネーションが動作することを確認"""
        api_key = os.environ.get('YOUTUBE_API_KEY')
        fetcher = YouTubeDataFetcher(api_key)
        
        # コメントが多い動画でテスト
        video_id = 'dQw4w9WgXcQ'
        comments = fetcher.fetch_comments(video_id, max_comments=150)
        
        # 100件以上取得できていることを確認（ページネーションが動作）
        assert len(comments) > 100
        assert len(comments) <= 150
    
    def test_invalid_video_id(self):
        """存在しない動画IDの処理を確認"""
        api_key = os.environ.get('YOUTUBE_API_KEY')
        fetcher = YouTubeDataFetcher(api_key)
        
        # 存在しない動画ID
        video_id = 'invalid_video_id_12345'
        video_info = fetcher.get_video_info(video_id)
        
        assert video_info['video_id'] == video_id
        assert video_info['published_at'] == ''
        
        # コメントも取得できない
        comments = fetcher.fetch_comments(video_id)
        assert len(comments) == 0