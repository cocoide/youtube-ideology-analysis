import csv
import sqlite3
from typing import List, Dict, Any
from pathlib import Path


class CSVStorage:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
    
    def save_comments(self, comments: List[Dict[str, Any]]) -> None:
        if not comments:
            return
            
        Path(self.csv_path).parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = [
            'videoId', 'videoPublishedAt', 'commentId', 
            'publishedAt', 'updatedAt', 'likeCount', 
            'totalReplyCount', 'text'
        ]
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(comments)


class SQLiteStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()
    
    def _create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                published_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                video_id TEXT,
                video_published_at TEXT,
                published_at TEXT,
                updated_at TEXT,
                like_count INTEGER,
                total_reply_count INTEGER,
                text TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_comments(self, comments: List[Dict[str, Any]]) -> None:
        if not comments:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        video_ids = set()
        for comment in comments:
            video_ids.add((comment['videoId'], comment['videoPublishedAt']))
        
        for video_id, published_at in video_ids:
            cursor.execute('''
                INSERT OR IGNORE INTO videos (video_id, published_at)
                VALUES (?, ?)
            ''', (video_id, published_at))
        
        for comment in comments:
            cursor.execute('''
                INSERT OR IGNORE INTO comments (
                    comment_id, video_id, video_published_at,
                    published_at, updated_at, like_count,
                    total_reply_count, text
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                comment['commentId'],
                comment['videoId'],
                comment['videoPublishedAt'],
                comment['publishedAt'],
                comment['updatedAt'],
                comment['likeCount'],
                comment['totalReplyCount'],
                comment['text']
            ))
        
        conn.commit()
        conn.close()