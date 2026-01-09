import pytest
from unittest.mock import Mock, MagicMock
from yt_pilot.api import YouTubeDataFetcher


class TestYouTubeDataFetcher:
    def test_pagination_with_limit(self, mocker):
        mock_youtube = MagicMock()
        mocker.patch('yt_pilot.api.build', return_value=mock_youtube)
        
        mock_request = MagicMock()
        
        page1_response = {
            'items': [
                {
                    'id': f'comment_{i}',
                    'snippet': {
                        'topLevelComment': {
                            'id': f'comment_{i}',
                            'snippet': {
                                'videoId': 'test_video',
                                'textDisplay': f'Comment {i}',
                                'publishedAt': '2024-01-01T00:00:00Z',
                                'updatedAt': '2024-01-01T00:00:00Z',
                                'likeCount': i,
                            }
                        },
                        'totalReplyCount': 0
                    }
                } for i in range(100)
            ],
            'nextPageToken': 'page2_token'
        }
        
        page2_response = {
            'items': [
                {
                    'id': f'comment_{i}',
                    'snippet': {
                        'topLevelComment': {
                            'id': f'comment_{i}',
                            'snippet': {
                                'videoId': 'test_video',
                                'textDisplay': f'Comment {i}',
                                'publishedAt': '2024-01-01T00:00:00Z',
                                'updatedAt': '2024-01-01T00:00:00Z',
                                'likeCount': i,
                            }
                        },
                        'totalReplyCount': 0
                    }
                } for i in range(100, 200)
            ],
            'nextPageToken': 'page3_token'
        }
        
        page3_response = {
            'items': [
                {
                    'id': f'comment_{i}',
                    'snippet': {
                        'topLevelComment': {
                            'id': f'comment_{i}',
                            'snippet': {
                                'videoId': 'test_video',
                                'textDisplay': f'Comment {i}',
                                'publishedAt': '2024-01-01T00:00:00Z',
                                'updatedAt': '2024-01-01T00:00:00Z',
                                'likeCount': i,
                            }
                        },
                        'totalReplyCount': 0
                    }
                } for i in range(200, 300)
            ]
        }
        
        execute_responses = [page1_response, page2_response, page3_response]
        mock_request.execute.side_effect = execute_responses
        mock_youtube.commentThreads().list.return_value = mock_request
        
        fetcher = YouTubeDataFetcher(api_key='test_key')
        comments = fetcher.fetch_comments('test_video', max_comments=150)
        
        assert len(comments) == 150
        assert comments[0]['commentId'] == 'comment_0'
        assert comments[149]['commentId'] == 'comment_149'
    
    def test_pagination_until_no_next_page_token(self, mocker):
        mock_youtube = MagicMock()
        mocker.patch('yt_pilot.api.build', return_value=mock_youtube)
        
        mock_request = MagicMock()
        
        page1_response = {
            'items': [
                {
                    'id': f'comment_{i}',
                    'snippet': {
                        'topLevelComment': {
                            'id': f'comment_{i}',
                            'snippet': {
                                'videoId': 'test_video',
                                'textDisplay': f'Comment {i}',
                                'publishedAt': '2024-01-01T00:00:00Z',
                                'updatedAt': '2024-01-01T00:00:00Z',
                                'likeCount': i,
                            }
                        },
                        'totalReplyCount': 0
                    }
                } for i in range(50)
            ]
        }
        
        mock_request.execute.return_value = page1_response
        mock_youtube.commentThreads().list.return_value = mock_request
        
        fetcher = YouTubeDataFetcher(api_key='test_key')
        comments = fetcher.fetch_comments('test_video', max_comments=500)
        
        assert len(comments) == 50
    
    def test_empty_video_list_response(self, mocker):
        mock_youtube = MagicMock()
        mocker.patch('yt_pilot.api.build', return_value=mock_youtube)
        
        mock_request = MagicMock()
        mock_request.execute.return_value = {'items': []}
        mock_youtube.videos().list.return_value = mock_request
        
        fetcher = YouTubeDataFetcher(api_key='test_key')
        video_info = fetcher.get_video_info('test_video')
        
        assert video_info['video_id'] == 'test_video'
        assert video_info['published_at'] == ''
    
    def test_comment_threads_exception_handling(self, mocker):
        mock_youtube = MagicMock()
        mocker.patch('yt_pilot.api.build', return_value=mock_youtube)
        
        mock_request = MagicMock()
        mock_request.execute.side_effect = Exception('Comments are disabled')
        mock_youtube.commentThreads().list.return_value = mock_request
        
        fetcher = YouTubeDataFetcher(api_key='test_key')
        comments = fetcher.fetch_comments('test_video')
        
        assert len(comments) == 0