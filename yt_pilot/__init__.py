"""YouTube Pilot - A tool for collecting and analyzing YouTube comments"""

from .api import YouTubeDataFetcher
from .storage import CSVStorage, SQLiteStorage
from .models import VideoInfo, Comment
from .collectors import VideoCommentCollector, DatasetBuilder
from .analysis import CommentAnalyzer, VideoCommentTrends

__version__ = "0.1.0"

__all__ = [
    'YouTubeDataFetcher',
    'CSVStorage', 
    'SQLiteStorage',
    'VideoInfo',
    'Comment',
    'VideoCommentCollector',
    'DatasetBuilder',
    'CommentAnalyzer',
    'VideoCommentTrends'
]