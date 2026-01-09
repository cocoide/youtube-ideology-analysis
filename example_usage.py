"""Example usage of yt_pilot library for research"""

import os
from dotenv import load_dotenv
from yt_pilot import (
    VideoCommentCollector, 
    DatasetBuilder,
    CommentAnalyzer,
    VideoCommentTrends
)
from yt_pilot.models import Comment

load_dotenv()


def example_basic_collection():
    """Example: Basic comment collection"""
    api_key = os.environ.get('YOUTUBE_API_KEY')
    collector = VideoCommentCollector(api_key)
    
    # Collect from single video
    result = collector.collect_video_comments(
        video_id='hj50Suuh5DM',
        max_comments=50
    )
    
    print(f"Collected {len(result['comments'])} comments")
    
    # Analyze
    analyzer = CommentAnalyzer(result['comments'])
    stats = analyzer.basic_stats()
    print(f"Average likes: {stats['avg_likes']:.2f}")
    print(f"Average text length: {stats['avg_text_length']:.1f} chars")


def example_batch_collection():
    """Example: Batch collection with metadata"""
    api_key = os.environ.get('YOUTUBE_API_KEY')
    collector = VideoCommentCollector(api_key, max_workers=3)
    builder = DatasetBuilder(collector)
    
    # Video IDs with metadata
    video_ids = ['hj50Suuh5DM', 'dQw4w9WgXcQ']
    metadata = {
        'hj50Suuh5DM': {
            'title': '【4分でわかる】選挙行かないと日本はこうなる',
            'category': '政治'
        },
        'dQw4w9WgXcQ': {
            'title': 'Rick Astley - Never Gonna Give You Up',
            'category': '音楽'
        }
    }
    
    # Progress callback
    def progress(video_id, current, total):
        print(f"Progress: {current}/{total} - Completed {video_id}")
    
    collector.set_progress_callback(progress)
    
    # Build dataset
    dataset_info = builder.build_dataset(
        video_ids=video_ids,
        output_csv='out/research_dataset.csv',
        output_db='out/research_dataset.sqlite',
        max_comments_per_video=100,
        metadata=metadata
    )
    
    print(f"\nDataset built:")
    print(f"Total videos: {dataset_info['total_videos']}")
    print(f"Total comments: {dataset_info['total_comments']}")


def example_analysis():
    """Example: Analyze collected comments"""
    # Assuming we have some comments loaded
    api_key = os.environ.get('YOUTUBE_API_KEY')
    collector = VideoCommentCollector(api_key)
    
    results = collector.collect_multiple_videos(
        ['hj50Suuh5DM'],
        max_comments_per_video=100
    )
    
    for result in results:
        if result['comments']:
            analyzer = CommentAnalyzer(result['comments'])
            
            print(f"\nAnalysis for video {result['video_id']}:")
            
            # Basic stats
            stats = analyzer.basic_stats()
            print(f"Total comments: {stats['total_comments']}")
            print(f"Avg/Max likes: {stats['avg_likes']:.1f} / {stats['max_likes']}")
            
            # Engagement
            engagement = analyzer.engagement_analysis()
            print(f"Reply rate: {engagement['reply_rate']:.2%}")
            
            # Text patterns
            patterns = analyzer.text_patterns()
            print(f"Questions: {patterns['question_rate']:.2%}")
            print(f"Emoji usage: {patterns['emoji_rate']:.2%}")
            
            # Top comments
            print("\nTop 3 comments by likes:")
            for i, comment in enumerate(analyzer.top_comments(3), 1):
                print(f"{i}. [{comment.like_count} likes] {comment.text[:80]}...")


if __name__ == '__main__':
    print("=== Basic Collection Example ===")
    example_basic_collection()
    
    print("\n\n=== Batch Collection Example ===")
    example_batch_collection()
    
    print("\n\n=== Analysis Example ===")
    example_analysis()