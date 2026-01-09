#!/usr/bin/env python3
"""サンプル動画のコメントを収集するスクリプト"""

import csv
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yt_pilot.api import YouTubeDataFetcher
from yt_pilot.storage import CSVStorage, SQLiteStorage

load_dotenv()


def read_sample_videos(csv_path):
    """サンプル動画のリストをCSVから読み込む"""
    videos = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            videos.append(row)
    return videos


def main():
    # APIキーの確認
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable is not set")
        sys.exit(1)
    
    # サンプル動画リストの読み込み
    sample_videos = read_sample_videos('sample_videos.csv')
    
    # 出力ディレクトリの作成
    os.makedirs('out/samples', exist_ok=True)
    
    # タイムスタンプ付きファイル名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    fetcher = YouTubeDataFetcher(api_key)
    
    for video_data in sample_videos:
        video_id = video_data['video_id']
        print(f"\n{'='*60}")
        print(f"Processing: {video_data['title']}")
        print(f"Video ID: {video_id}")
        print(f"Category: {video_data['category']}")
        print(f"{'='*60}")
        
        # 動画情報の取得
        video_info = fetcher.get_video_info(video_id)
        print(f"Published at: {video_info['published_at']}")
        
        # コメントの取得
        comments = fetcher.fetch_comments(video_id, max_comments=100)
        print(f"Fetched {len(comments)} comments")
        
        # メタデータの追加
        for comment in comments:
            comment['videoPublishedAt'] = video_info['published_at']
            comment['videoTitle'] = video_data['title']
            comment['videoCategory'] = video_data['category']
        
        # 個別CSV保存（動画ごと）
        csv_path = f"out/samples/{video_id}_{timestamp}.csv"
        csv_storage = CSVStorage(csv_path)
        
        # 拡張フィールドを含むコメントデータを保存
        if comments:
            fieldnames = list(comments[0].keys())
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(comments)
        
        print(f"Saved to: {csv_path}")
        
        # 統合データベースに保存
        db_path = f"out/samples/all_samples_{timestamp}.sqlite"
        db_storage = SQLiteStorage(db_path)
        
        # 基本フィールドのみでDB保存
        basic_comments = []
        for c in comments:
            basic_comments.append({
                'videoId': c['videoId'],
                'videoPublishedAt': c['videoPublishedAt'],
                'commentId': c['commentId'],
                'publishedAt': c['publishedAt'],
                'updatedAt': c['updatedAt'],
                'likeCount': c['likeCount'],
                'totalReplyCount': c['totalReplyCount'],
                'text': c['text']
            })
        
        db_storage.save_comments(basic_comments)
        print(f"Added to database: {db_path}")
    
    print(f"\n{'='*60}")
    print("Collection complete!")
    print(f"Timestamp: {timestamp}")


if __name__ == '__main__':
    main()