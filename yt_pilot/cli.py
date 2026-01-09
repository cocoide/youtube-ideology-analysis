import os
import sys
import argparse
from dotenv import load_dotenv
from .api import YouTubeDataFetcher
from .storage import CSVStorage, SQLiteStorage
from .coding import create_coding_sheet
from .improved_coding import create_improved_coding_sheet
from .report import generate_report_cli
from .advanced_report import generate_advanced_report_cli


def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description='YouTube comment collection tool for thesis pilot study'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Collect command (original functionality)
    collect_parser = subparsers.add_parser('collect', help='Collect YouTube comments')
    collect_parser.add_argument(
        '--video', 
        action='append', 
        required=True, 
        help='Video ID (can be specified multiple times)'
    )
    collect_parser.add_argument(
        '--max-comments', 
        type=int, 
        default=500, 
        help='Maximum comments per video (default: 500)'
    )
    collect_parser.add_argument(
        '--order', 
        choices=['time', 'relevance'], 
        default='time', 
        help='Comment order (default: time)'
    )
    collect_parser.add_argument(
        '--csv', 
        help='CSV output path'
    )
    collect_parser.add_argument(
        '--db', 
        help='SQLite database output path'
    )
    
    # Make coding sheet command
    coding_parser = subparsers.add_parser('make-coding-sheet', help='Generate coding sheet from database')
    coding_parser.add_argument(
        '--db',
        required=True,
        help='SQLite database path'
    )
    coding_parser.add_argument(
        '--out',
        required=True,
        help='Output CSV path for coding sheet'
    )
    coding_parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of comments'
    )
    coding_parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducible sampling'
    )
    
    # Improved coding sheet command
    improved_parser = subparsers.add_parser('make-improved-coding-sheet', help='Generate improved coding sheet with priority rules')
    improved_parser.add_argument(
        '--db',
        required=True,
        help='SQLite database path'
    )
    improved_parser.add_argument(
        '--out',
        required=True,
        help='Output CSV path for improved coding sheet'
    )
    improved_parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of comments'
    )
    improved_parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducible sampling'
    )
    improved_parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Omit debug columns (priority rules and detected keywords)'
    )
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate analysis report from coded data')
    report_parser.add_argument(
        '--coded',
        required=True,
        help='Coded CSV file path'
    )
    report_parser.add_argument(
        '--out',
        required=True,
        help='Output directory for reports'
    )
    report_parser.add_argument(
        '--videos',
        help='Video metadata CSV (for frame information)'
    )
    
    # Advanced report command
    adv_parser = subparsers.add_parser('advanced-report', help='Generate advanced report with robustness checks')
    adv_parser.add_argument(
        '--coded',
        required=True,
        help='Coded CSV file path'
    )
    adv_parser.add_argument(
        '--out',
        required=True,
        help='Output directory for reports'
    )
    adv_parser.add_argument(
        '--videos',
        help='Video metadata CSV (for frame information)'
    )
    adv_parser.add_argument(
        '--days',
        type=int,
        default=14,
        help='Filter to N days after video publication (default: 14)'
    )
    
    args = parser.parse_args()
    
    # Handle different commands
    if args.command == 'collect':
        collect_comments(args)
    elif args.command == 'make-coding-sheet':
        create_coding_sheet(
            db_path=args.db,
            output_path=args.out,
            limit=args.limit,
            seed=args.seed
        )
    elif args.command == 'make-improved-coding-sheet':
        create_improved_coding_sheet(
            db_path=args.db,
            output_path=args.out,
            limit=args.limit,
            seed=args.seed,
            include_debug=not args.no_debug
        )
    elif args.command == 'report':
        generate_report_cli(
            coded_csv=args.coded,
            output_dir=args.out,
            video_csv=args.videos
        )
    elif args.command == 'advanced-report':
        generate_advanced_report_cli(
            coded_csv=args.coded,
            output_dir=args.out,
            video_csv=args.videos,
            days=args.days
        )
    else:
        parser.print_help()
        sys.exit(1)


def collect_comments(args):
    """Original collect functionality"""
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