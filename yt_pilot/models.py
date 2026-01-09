"""Data models for YouTube comment analysis"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class VideoInfo:
    """YouTube video information"""
    video_id: str
    published_at: str
    title: Optional[str] = None
    channel: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'video_id': self.video_id,
            'published_at': self.published_at,
            'title': self.title,
            'channel': self.channel,
            'description': self.description,
            'category': self.category,
            'tags': self.tags
        }


@dataclass
class Comment:
    """YouTube comment data"""
    comment_id: str
    video_id: str
    text: str
    published_at: str
    updated_at: str
    like_count: int
    total_reply_count: int
    video_published_at: Optional[str] = None
    
    # Extended metadata
    video_title: Optional[str] = None
    video_category: Optional[str] = None
    author_channel_id: Optional[str] = None
    
    def to_dict(self, include_extended: bool = False) -> Dict[str, Any]:
        """Convert to dictionary with optional extended fields"""
        base = {
            'commentId': self.comment_id,
            'videoId': self.video_id,
            'text': self.text,
            'publishedAt': self.published_at,
            'updatedAt': self.updated_at,
            'likeCount': self.like_count,
            'totalReplyCount': self.total_reply_count,
            'videoPublishedAt': self.video_published_at or ''
        }
        
        if include_extended:
            if self.video_title:
                base['videoTitle'] = self.video_title
            if self.video_category:
                base['videoCategory'] = self.video_category
            if self.author_channel_id:
                base['authorChannelId'] = self.author_channel_id
                
        return base
    
    @classmethod
    def from_api_response(cls, item: Dict[str, Any], video_id: str) -> 'Comment':
        """Create Comment from YouTube API response"""
        comment_data = item['snippet']['topLevelComment']['snippet']
        return cls(
            comment_id=item['id'],
            video_id=video_id,
            text=comment_data.get('textDisplay', ''),
            published_at=comment_data.get('publishedAt', ''),
            updated_at=comment_data.get('updatedAt', ''),
            like_count=comment_data.get('likeCount', 0),
            total_reply_count=item['snippet'].get('totalReplyCount', 0),
            author_channel_id=comment_data.get('authorChannelId')
        )