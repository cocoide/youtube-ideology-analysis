"""High-level collectors for batch operations"""

import logging
from typing import List, Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from .api import YouTubeDataFetcher
from .models import VideoInfo, Comment
from .storage import CSVStorage, SQLiteStorage


logger = logging.getLogger(__name__)


class VideoCommentCollector:
    """Batch collector for multiple videos with progress tracking"""
    
    def __init__(self, api_key: str, max_workers: int = 3):
        self.fetcher = YouTubeDataFetcher(api_key)
        self.max_workers = max_workers
        self._progress_callback: Optional[Callable] = None
    
    def set_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Set callback for progress updates (video_id, current, total)"""
        self._progress_callback = callback
    
    def collect_video_comments(
        self,
        video_id: str,
        max_comments: int = 500,
        order: str = 'time',
        include_video_info: bool = True
    ) -> Dict[str, Any]:
        """Collect comments for a single video"""
        result = {
            'video_id': video_id,
            'video_info': None,
            'comments': [],
            'error': None
        }
        
        try:
            # Get video info
            if include_video_info:
                video_info_dict = self.fetcher.get_video_info(video_id)
                result['video_info'] = VideoInfo(
                    video_id=video_id,
                    published_at=video_info_dict['published_at']
                )
            
            # Get comments
            comment_dicts = self.fetcher.fetch_comments(video_id, max_comments, order)
            comments = []
            
            for cd in comment_dicts:
                comment = Comment(
                    comment_id=cd['commentId'],
                    video_id=cd['videoId'],
                    text=cd['text'],
                    published_at=cd['publishedAt'],
                    updated_at=cd['updatedAt'],
                    like_count=cd['likeCount'],
                    total_reply_count=cd['totalReplyCount'],
                    video_published_at=cd.get('videoPublishedAt', '')
                )
                comments.append(comment)
            
            result['comments'] = comments
            
        except Exception as e:
            logger.error(f"Error collecting video {video_id}: {e}")
            result['error'] = str(e)
            
        return result
    
    def collect_multiple_videos(
        self,
        video_ids: List[str],
        max_comments_per_video: int = 500,
        order: str = 'time'
    ) -> List[Dict[str, Any]]:
        """Collect comments from multiple videos in parallel"""
        results = []
        total = len(video_ids)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_video = {
                executor.submit(
                    self.collect_video_comments,
                    video_id,
                    max_comments_per_video,
                    order
                ): video_id
                for video_id in video_ids
            }
            
            for i, future in enumerate(as_completed(future_to_video)):
                video_id = future_to_video[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if self._progress_callback:
                        self._progress_callback(video_id, i + 1, total)
                        
                except Exception as e:
                    logger.error(f"Error processing {video_id}: {e}")
                    results.append({
                        'video_id': video_id,
                        'video_info': None,
                        'comments': [],
                        'error': str(e)
                    })
        
        return results


class DatasetBuilder:
    """Build datasets with consistent structure for analysis"""
    
    def __init__(self, collector: VideoCommentCollector):
        self.collector = collector
    
    def build_dataset(
        self,
        video_ids: List[str],
        output_csv: Optional[str] = None,
        output_db: Optional[str] = None,
        max_comments_per_video: int = 500,
        metadata: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build a complete dataset from video IDs"""
        
        # Collect data
        results = self.collector.collect_multiple_videos(
            video_ids, max_comments_per_video
        )
        
        # Process and enrich with metadata
        all_comments = []
        video_stats = []
        
        for result in results:
            video_id = result['video_id']
            comments = result['comments']
            
            # Add metadata if available
            if metadata and video_id in metadata:
                meta = metadata[video_id]
                for comment in comments:
                    comment.video_title = meta.get('title')
                    comment.video_category = meta.get('category')
            
            all_comments.extend(comments)
            
            video_stats.append({
                'video_id': video_id,
                'comment_count': len(comments),
                'error': result.get('error')
            })
        
        # Save to storage
        if output_csv:
            csv_storage = CSVStorage(output_csv)
            comment_dicts = [c.to_dict(include_extended=True) for c in all_comments]
            csv_storage.save_comments(comment_dicts)
        
        if output_db:
            db_storage = SQLiteStorage(output_db)
            comment_dicts = [c.to_dict(include_extended=False) for c in all_comments]
            db_storage.save_comments(comment_dicts)
        
        return {
            'total_videos': len(video_ids),
            'total_comments': len(all_comments),
            'video_stats': video_stats,
            'output_csv': output_csv,
            'output_db': output_db
        }