#!/usr/bin/env python3
"""全サンプル動画のコメントを収集"""

import os
import sys
import csv
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yt_pilot import VideoCommentCollector, DatasetBuilder

load_dotenv()


def main():
    # Read sample videos
    with open('sample_videos.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        videos = list(reader)
    
    # Get API key
    api_key = os.environ.get('YOUTUBE_API_KEY')
    if not api_key:
        print("Error: YOUTUBE_API_KEY environment variable is not set")
        sys.exit(1)
    
    # Create collector and builder
    collector = VideoCommentCollector(api_key)
    builder = DatasetBuilder(collector)
    
    # Progress callback
    def progress(video_id, current, total):
        video_title = next((v['title'] for v in videos if v['video_id'] == video_id), video_id)
        print(f"[{current}/{total}] Completed: {video_title[:50]}...")
    
    collector.set_progress_callback(progress)
    
    # Extract video IDs and metadata
    video_ids = [v['video_id'] for v in videos]
    metadata = {
        v['video_id']: {
            'title': v['title'],
            'category': v['category'],
            'frame': v['frame']
        }
        for v in videos
    }
    
    # Create output directory
    os.makedirs('out', exist_ok=True)
    
    # Build dataset
    print("Collecting comments from sample videos...")
    print(f"Videos: {len(video_ids)}")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    dataset_info = builder.build_dataset(
        video_ids=video_ids,
        output_csv=f'out/all_comments_{timestamp}.csv',
        output_db=f'out/all_comments_{timestamp}.sqlite',
        max_comments_per_video=500,
        metadata=metadata
    )
    
    print("\n" + "="*60)
    print("Collection Summary:")
    print(f"Total videos processed: {dataset_info['total_videos']}")
    print(f"Total comments collected: {dataset_info['total_comments']}")
    
    print("\nPer video breakdown:")
    for stat in dataset_info['video_stats']:
        video_title = metadata.get(stat['video_id'], {}).get('title', stat['video_id'])
        frame = metadata.get(stat['video_id'], {}).get('frame', 'Unknown')
        print(f"  [{frame}] {video_title[:40]}... : {stat['comment_count']} comments")
        if stat.get('error'):
            print(f"    Error: {stat['error']}")
    
    print(f"\nOutputs:")
    print(f"  CSV: {dataset_info['output_csv']}")
    print(f"  Database: {dataset_info['output_db']}")


if __name__ == '__main__':
    main()