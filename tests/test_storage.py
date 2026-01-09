import tempfile
import csv
import sqlite3
from pathlib import Path
from yt_pilot.storage import CSVStorage, SQLiteStorage


class TestCSVStorage:
    def test_csv_output_with_headers(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            csv_path = tmp.name
        
        try:
            comments = [
                {
                    'videoId': 'video1',
                    'videoPublishedAt': '2024-01-01T00:00:00Z',
                    'commentId': 'comment1',
                    'publishedAt': '2024-01-02T00:00:00Z',
                    'updatedAt': '2024-01-02T01:00:00Z',
                    'likeCount': 10,
                    'totalReplyCount': 2,
                    'text': 'Test comment 1'
                },
                {
                    'videoId': 'video1',
                    'videoPublishedAt': '2024-01-01T00:00:00Z',
                    'commentId': 'comment2',
                    'publishedAt': '2024-01-02T02:00:00Z',
                    'updatedAt': '2024-01-02T03:00:00Z',
                    'likeCount': 5,
                    'totalReplyCount': 0,
                    'text': 'Test comment 2'
                }
            ]
            
            storage = CSVStorage(csv_path)
            storage.save_comments(comments)
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 2
            assert rows[0]['commentId'] == 'comment1'
            assert rows[0]['text'] == 'Test comment 1'
            assert rows[1]['commentId'] == 'comment2'
            assert rows[1]['text'] == 'Test comment 2'
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    def test_csv_handles_special_characters(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp:
            csv_path = tmp.name
        
        try:
            comments = [
                {
                    'videoId': 'video1',
                    'videoPublishedAt': '2024-01-01T00:00:00Z',
                    'commentId': 'comment1',
                    'publishedAt': '2024-01-02T00:00:00Z',
                    'updatedAt': '2024-01-02T01:00:00Z',
                    'likeCount': 10,
                    'totalReplyCount': 0,
                    'text': 'Comment with\nnewlines,commas,and "quotes"'
                }
            ]
            
            storage = CSVStorage(csv_path)
            storage.save_comments(comments)
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 1
            assert rows[0]['text'] == 'Comment with\nnewlines,commas,and "quotes"'
            
        finally:
            Path(csv_path).unlink(missing_ok=True)


class TestSQLiteStorage:
    def test_sqlite_creates_tables(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            storage = SQLiteStorage(db_path)
            storage._create_tables()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'videos' in tables
            assert 'comments' in tables
            
            conn.close()
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    def test_sqlite_no_duplicate_insertion(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp:
            db_path = tmp.name
        
        try:
            comments = [
                {
                    'videoId': 'video1',
                    'videoPublishedAt': '2024-01-01T00:00:00Z',
                    'commentId': 'comment1',
                    'publishedAt': '2024-01-02T00:00:00Z',
                    'updatedAt': '2024-01-02T01:00:00Z',
                    'likeCount': 10,
                    'totalReplyCount': 2,
                    'text': 'Test comment 1'
                },
                {
                    'videoId': 'video1',
                    'videoPublishedAt': '2024-01-01T00:00:00Z',
                    'commentId': 'comment2',
                    'publishedAt': '2024-01-02T02:00:00Z',
                    'updatedAt': '2024-01-02T03:00:00Z',
                    'likeCount': 5,
                    'totalReplyCount': 0,
                    'text': 'Test comment 2'
                }
            ]
            
            storage = SQLiteStorage(db_path)
            storage.save_comments(comments)
            storage.save_comments(comments)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM comments")
            comment_count = cursor.fetchone()[0]
            assert comment_count == 2
            
            cursor.execute("SELECT COUNT(*) FROM videos")
            video_count = cursor.fetchone()[0]
            assert video_count == 1
            
            conn.close()
            
        finally:
            Path(db_path).unlink(missing_ok=True)