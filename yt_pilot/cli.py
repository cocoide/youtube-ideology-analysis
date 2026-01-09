import os
import sys
import argparse
from dotenv import load_dotenv
from .api import YouTubeDataFetcher
from .storage import CSVStorage, SQLiteStorage


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='YouTube comment collection tool for thesis pilot study'
    )
    parser.add_argument(
        '--video', 
        action='append', 
        required=True, 
        help='Video ID (can be specified multiple times)'
    )
    parser.add_argument(
        '--max-comments', 
        type=int, 
        default=500, 
        help='Maximum comments per video (default: 500)'
    )
    parser.add_argument(
        '--order', 
        choices=['time', 'relevance'], 
        default='time', 
        help='Comment order (default: time)'
    )
    parser.add_argument(
        '--csv', 
        help='CSV output path'
    )
    parser.add_argument(
        '--db', 
        help='SQLite database output path'
    )
    
    args = parser.parse_args()
    
    if not args.csv and not args.db:
        print("Error: At least one output format (--csv or --db) must be specified")
        sys.exit(1)
    
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable is not set")
        print("Please set it with: export YOUTUBE_API_KEY='your-api-key'")
        sys.exit(1)
    
    fetcher = YouTubeDataFetcher(api_key)
    csv_storage = CSVStorage(args.csv) if args.csv else None
    db_storage = SQLiteStorage(args.db) if args.db else None
    
    all_comments = []
    
    for video_id in args.video:
        print(f"\nProcessing video: {video_id}")
        
        video_info = fetcher.get_video_info(video_id)
        
        comments = fetcher.fetch_comments(
            video_id, 
            max_comments=args.max_comments, 
            order=args.order
        )
        
        for comment in comments:
            comment['videoPublishedAt'] = video_info['published_at']
        
        all_comments.extend(comments)
        
        if db_storage:
            existing_count = count_existing_comments(db_storage, video_id)
            db_storage.save_comments(comments)
            new_count = count_existing_comments(db_storage, video_id)
            skipped = len(comments) - (new_count - existing_count)
            
            print(f"  Fetched: {len(comments)} comments")
            print(f"  Saved: {new_count - existing_count} new comments")
            print(f"  Skipped: {skipped} duplicate comments")
        else:
            print(f"  Fetched: {len(comments)} comments")
        
    
    if csv_storage:
        csv_storage.save_comments(all_comments)
        print(f"CSV saved to: {args.csv}")
    
    print(f"\nTotal comments collected: {len(all_comments)}")
    
    if args.db:
        print(f"Database saved to: {args.db}")


def count_existing_comments(db_storage: SQLiteStorage, video_id: str) -> int:
    import sqlite3
    conn = sqlite3.connect(db_storage.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM comments WHERE video_id = ?", (video_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


if __name__ == '__main__':
    main()