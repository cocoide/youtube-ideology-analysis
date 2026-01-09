from typing import List, Dict, Any
from googleapiclient.discovery import build


class YouTubeDataFetcher:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)
    
    def get_video_info(self, video_id: str) -> Dict[str, str]:
        try:
            request = self.youtube.videos().list(
                part='snippet',
                id=video_id
            )
            response = request.execute()
            
            if response.get('items'):
                video_data = response['items'][0]['snippet']
                return {
                    'video_id': video_id,
                    'published_at': video_data.get('publishedAt', '')
                }
            else:
                return {
                    'video_id': video_id,
                    'published_at': ''
                }
        except Exception as e:
            print(f"Error fetching video info for {video_id}: {e}")
            return {
                'video_id': video_id,
                'published_at': ''
            }
    
    def fetch_comments(self, video_id: str, max_comments: int = 500, order: str = 'time') -> List[Dict[str, Any]]:
        comments = []
        page_token = None
        
        try:
            while len(comments) < max_comments:
                request = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_comments - len(comments)),
                    order=order,
                    pageToken=page_token,
                    textFormat='plainText'
                )
                
                response = request.execute()
                
                for item in response.get('items', []):
                    comment_data = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'videoId': video_id,
                        'videoPublishedAt': '',
                        'commentId': item['id'],
                        'publishedAt': comment_data.get('publishedAt', ''),
                        'updatedAt': comment_data.get('updatedAt', ''),
                        'likeCount': comment_data.get('likeCount', 0),
                        'totalReplyCount': item['snippet'].get('totalReplyCount', 0),
                        'text': comment_data.get('textDisplay', '')
                    })
                    
                    if len(comments) >= max_comments:
                        break
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                    
        except Exception as e:
            print(f"Error fetching comments for video {video_id}: {e}")
            
        return comments