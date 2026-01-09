"""Basic analysis utilities for YouTube comments"""

import statistics
from typing import List, Dict, Any, Tuple
from collections import Counter
from datetime import datetime
from .models import Comment


class CommentAnalyzer:
    """Basic statistical analysis for comments"""
    
    def __init__(self, comments: List[Comment]):
        self.comments = comments
    
    def basic_stats(self) -> Dict[str, Any]:
        """Calculate basic statistics"""
        if not self.comments:
            return {
                'total_comments': 0,
                'avg_likes': 0,
                'max_likes': 0,
                'avg_replies': 0,
                'max_replies': 0,
                'avg_text_length': 0
            }
        
        like_counts = [c.like_count for c in self.comments]
        reply_counts = [c.total_reply_count for c in self.comments]
        text_lengths = [len(c.text) for c in self.comments]
        
        return {
            'total_comments': len(self.comments),
            'avg_likes': statistics.mean(like_counts),
            'median_likes': statistics.median(like_counts),
            'max_likes': max(like_counts),
            'avg_replies': statistics.mean(reply_counts),
            'max_replies': max(reply_counts),
            'avg_text_length': statistics.mean(text_lengths),
            'min_text_length': min(text_lengths),
            'max_text_length': max(text_lengths)
        }
    
    def temporal_distribution(self) -> Dict[str, int]:
        """Analyze comment distribution over time"""
        date_counts = Counter()
        
        for comment in self.comments:
            try:
                date = datetime.fromisoformat(comment.published_at.replace('Z', '+00:00'))
                date_key = date.strftime('%Y-%m-%d')
                date_counts[date_key] += 1
            except:
                continue
                
        return dict(sorted(date_counts.items()))
    
    def engagement_analysis(self) -> Dict[str, Any]:
        """Analyze engagement patterns"""
        # High engagement comments (top 10%)
        sorted_by_likes = sorted(self.comments, key=lambda c: c.like_count, reverse=True)
        top_10_percent = int(len(self.comments) * 0.1) or 1
        
        high_engagement = sorted_by_likes[:top_10_percent]
        
        # Comments with replies
        with_replies = [c for c in self.comments if c.total_reply_count > 0]
        
        return {
            'high_engagement_comments': len(high_engagement),
            'high_engagement_avg_likes': statistics.mean([c.like_count for c in high_engagement]),
            'comments_with_replies': len(with_replies),
            'reply_rate': len(with_replies) / len(self.comments) if self.comments else 0,
            'avg_replies_when_present': statistics.mean([c.total_reply_count for c in with_replies]) if with_replies else 0
        }
    
    def top_comments(self, n: int = 10, by: str = 'likes') -> List[Comment]:
        """Get top N comments by specified metric"""
        if by == 'likes':
            return sorted(self.comments, key=lambda c: c.like_count, reverse=True)[:n]
        elif by == 'replies':
            return sorted(self.comments, key=lambda c: c.total_reply_count, reverse=True)[:n]
        elif by == 'length':
            return sorted(self.comments, key=lambda c: len(c.text), reverse=True)[:n]
        else:
            raise ValueError(f"Unknown sort criteria: {by}")
    
    def text_patterns(self) -> Dict[str, Any]:
        """Analyze text patterns (simple version)"""
        # Question comments
        questions = [c for c in self.comments if '?' in c.text or '？' in c.text]
        
        # Exclamation comments  
        exclamations = [c for c in self.comments if '!' in c.text or '！' in c.text]
        
        # URL mentions
        urls = [c for c in self.comments if 'http' in c.text or 'www.' in c.text]
        
        # Emoji usage (simple check)
        import re
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            "]+", flags=re.UNICODE)
        
        with_emoji = [c for c in self.comments if emoji_pattern.search(c.text)]
        
        return {
            'question_comments': len(questions),
            'question_rate': len(questions) / len(self.comments) if self.comments else 0,
            'exclamation_comments': len(exclamations),
            'exclamation_rate': len(exclamations) / len(self.comments) if self.comments else 0,
            'url_mentions': len(urls),
            'emoji_usage': len(with_emoji),
            'emoji_rate': len(with_emoji) / len(self.comments) if self.comments else 0
        }


class VideoCommentTrends:
    """Analyze trends across multiple videos"""
    
    def __init__(self, video_results: List[Dict[str, Any]]):
        self.video_results = video_results
    
    def compare_videos(self) -> List[Dict[str, Any]]:
        """Compare key metrics across videos"""
        comparisons = []
        
        for result in self.video_results:
            if result.get('error'):
                continue
                
            comments = result['comments']
            if not comments:
                continue
                
            analyzer = CommentAnalyzer(comments)
            stats = analyzer.basic_stats()
            engagement = analyzer.engagement_analysis()
            
            comparisons.append({
                'video_id': result['video_id'],
                'total_comments': stats['total_comments'],
                'avg_likes': stats['avg_likes'],
                'max_likes': stats['max_likes'],
                'reply_rate': engagement['reply_rate'],
                'high_engagement_rate': engagement['high_engagement_comments'] / stats['total_comments'] if stats['total_comments'] > 0 else 0
            })
        
        return sorted(comparisons, key=lambda x: x['avg_likes'], reverse=True)