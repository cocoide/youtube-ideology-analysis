import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from yt_pilot.advanced_report import (
    filter_by_days_since_video,
    perform_loo_analysis,
    calculate_engagement_metrics,
    AdvancedReportGenerator
)


class TestAdvancedReport:
    def create_test_data(self):
        """テスト用データを作成"""
        # Video publish dates
        video_published = {
            'v1': '2024-01-01T00:00:00Z',
            'v2': '2024-01-01T00:00:00Z',
            'v3': '2024-01-15T00:00:00Z',
            'v4': '2024-01-15T00:00:00Z',
        }
        
        data = []
        for vid in ['v1', 'v2', 'v3', 'v4']:
            frame = 'Loss' if vid in ['v1', 'v2'] else 'Gain'
            base_date = datetime.fromisoformat(video_published[vid].replace('Z', '+00:00'))
            
            for i in range(25):
                # Comments spread over 30 days
                days_after = i % 20
                comment_date = base_date + timedelta(days=days_after)
                
                data.append({
                    'video_id': vid,
                    'comment_id': f'{vid}_c{i}',
                    'frame': frame,
                    'video_published_at': video_published[vid],
                    'published_at': comment_date.strftime('%Y-%m-%dT%H:%M:%S') + 'Z',
                    'like_count': np.random.poisson(2),
                    'total_reply_count': 1 if np.random.random() < 0.2 else 0,
                    'VP': '1' if np.random.random() < (0.3 if frame == 'Loss' else 0.2) else '0',
                    'E_int': '1' if np.random.random() < 0.25 else '0',
                    'E_ext': '1' if np.random.random() < (0.2 if frame == 'Loss' else 0.4) else '0',
                    'Cyn': '1' if np.random.random() < (0.4 if frame == 'Loss' else 0.2) else '0',
                    'Norm': '0',
                    'Info': '0',
                })
        
        return pd.DataFrame(data)
    
    def test_filter_by_days_since_video(self):
        """動画公開後N日以内のフィルタリングテスト"""
        df = self.create_test_data()
        
        # Filter to 14 days
        filtered = filter_by_days_since_video(df, days=14)
        
        # Check all comments are within 14 days
        for _, row in filtered.iterrows():
            video_date = pd.to_datetime(row['video_published_at'])
            comment_date = pd.to_datetime(row['published_at'])
            days_diff = (comment_date - video_date).days
            assert days_diff <= 14
        
        # Should have fewer comments than original
        assert len(filtered) < len(df)
        assert len(filtered) > 0
    
    def test_perform_loo_analysis(self):
        """Leave-One-Out分析のテスト"""
        df = self.create_test_data()
        
        loo_results = perform_loo_analysis(df)
        
        # Check structure
        assert 'excluded_video' in loo_results.columns
        assert 'H1_p_value' in loo_results.columns
        assert 'H1_effect_size' in loo_results.columns
        assert 'H2_p_value' in loo_results.columns
        assert 'H2_effect_size' in loo_results.columns
        
        # Should have one row per video + all videos
        unique_videos = df['video_id'].unique()
        assert len(loo_results) == len(unique_videos) + 1
        
        # Check 'none' (all videos) is included
        assert 'none' in loo_results['excluded_video'].values
    
    def test_calculate_engagement_metrics(self):
        """エンゲージメント指標の計算テスト"""
        df = self.create_test_data()
        
        metrics = calculate_engagement_metrics(df)
        
        # Check structure
        assert 'has_like_rate' in metrics.columns
        assert 'has_reply_rate' in metrics.columns
        assert 'avg_like_if_any' in metrics.columns
        assert 'high_engagement_rate' in metrics.columns
        
        # Check values are reasonable
        for frame in ['Loss', 'Gain']:
            row = metrics.loc[frame]
            assert 0 <= row['has_like_rate'] <= 1
            assert 0 <= row['has_reply_rate'] <= 1
            assert row['avg_like_if_any'] >= 0
    
    def test_advanced_report_generator(self):
        """統合レポート生成テスト"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            df = self.create_test_data()
            input_file = Path(tmpdir) / 'coded.csv'
            df.to_csv(input_file, index=False)
            
            # Generate report
            generator = AdvancedReportGenerator()
            generator.generate_advanced_report(
                str(input_file),
                output_dir=tmpdir,
                days_filter=14,
                include_loo=True,
                include_engagement=True
            )
            
            # Check outputs exist
            assert (Path(tmpdir) / 'summary_14days.csv').exists()
            assert (Path(tmpdir) / 'loo_analysis.csv').exists()
            assert (Path(tmpdir) / 'engagement_metrics.csv').exists()
            assert (Path(tmpdir) / 'robustness_report.txt').exists()
    
    def test_robustness_interpretation(self):
        """頑健性解釈のテスト"""
        # Create LOO results with varying p-values
        loo_data = pd.DataFrame([
            {'excluded_video': 'none', 'H1_p_value': 0.04, 'H1_effect_size': 0.08, 'H2_p_value': 0.001, 'H2_effect_size': -0.20},
            {'excluded_video': 'v1', 'H1_p_value': 0.08, 'H1_effect_size': 0.06, 'H2_p_value': 0.002, 'H2_effect_size': -0.18},
            {'excluded_video': 'v2', 'H1_p_value': 0.03, 'H1_effect_size': 0.09, 'H2_p_value': 0.001, 'H2_effect_size': -0.21},
            {'excluded_video': 'v3', 'H1_p_value': 0.06, 'H1_effect_size': 0.07, 'H2_p_value': 0.0008, 'H2_effect_size': -0.22},
            {'excluded_video': 'v4', 'H1_p_value': 0.02, 'H1_effect_size': 0.10, 'H2_p_value': 0.003, 'H2_effect_size': -0.17},
        ])
        
        generator = AdvancedReportGenerator()
        interpretation = generator._interpret_robustness(loo_data)
        
        # H1 should be marked as sensitive (p-values vary around 0.05)
        assert 'sensitive' in interpretation.lower() or 'varies' in interpretation.lower()
        
        # H2 should be marked as robust (all p-values < 0.01)
        assert 'robust' in interpretation.lower() or 'consistent' in interpretation.lower()