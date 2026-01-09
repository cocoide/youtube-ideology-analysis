import pytest
import tempfile
import csv
import pandas as pd
from pathlib import Path
from yt_pilot.report import (
    ReportGenerator,
    calculate_frame_summary,
    calculate_video_summary,
    perform_hypothesis_tests
)


class TestReportGenerator:
    def create_test_coded_csv(self, csv_path: str):
        """テスト用のコーディング済みCSVを作成"""
        data = [
            # Loss frame videos
            {'video_id': 'v1', 'comment_id': 'c1', 'frame': 'Loss', 
             'VP': '1', 'E_int': '0', 'E_ext': '0', 'Cyn': '0', 'like_count': '10', 'total_reply_count': '0'},
            {'video_id': 'v1', 'comment_id': 'c2', 'frame': 'Loss', 
             'VP': '1', 'E_int': '0', 'E_ext': '0', 'Cyn': '1', 'like_count': '5', 'total_reply_count': '0'},
            {'video_id': 'v1', 'comment_id': 'c3', 'frame': 'Loss', 
             'VP': '0', 'E_int': '1', 'E_ext': '0', 'Cyn': '0', 'like_count': '0', 'total_reply_count': '0'},
            {'video_id': 'v2', 'comment_id': 'c4', 'frame': 'Loss', 
             'VP': '1', 'E_int': '0', 'E_ext': '1', 'Cyn': '0', 'like_count': '20', 'total_reply_count': '1'},
            {'video_id': 'v2', 'comment_id': 'c5', 'frame': 'Loss', 
             'VP': '0', 'E_int': '0', 'E_ext': '0', 'Cyn': '1', 'like_count': '2', 'total_reply_count': '0'},
            
            # Gain frame videos
            {'video_id': 'v3', 'comment_id': 'c6', 'frame': 'Gain', 
             'VP': '0', 'E_int': '0', 'E_ext': '1', 'Cyn': '0', 'like_count': '15', 'total_reply_count': '2'},
            {'video_id': 'v3', 'comment_id': 'c7', 'frame': 'Gain', 
             'VP': '0', 'E_int': '1', 'E_ext': '1', 'Cyn': '0', 'like_count': '8', 'total_reply_count': '0'},
            {'video_id': 'v3', 'comment_id': 'c8', 'frame': 'Gain', 
             'VP': '1', 'E_int': '0', 'E_ext': '0', 'Cyn': '0', 'like_count': '3', 'total_reply_count': '0'},
            {'video_id': 'v4', 'comment_id': 'c9', 'frame': 'Gain', 
             'VP': '0', 'E_int': '0', 'E_ext': '1', 'Cyn': '0', 'like_count': '25', 'total_reply_count': '3'},
            {'video_id': 'v4', 'comment_id': 'c10', 'frame': 'Gain', 
             'VP': '0', 'E_int': '1', 'E_ext': '0', 'Cyn': '0', 'like_count': '1', 'total_reply_count': '0'},
        ]
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['video_id', 'comment_id', 'frame', 'VP', 'E_int', 'E_ext', 'Cyn', 'like_count', 'total_reply_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def test_calculate_frame_summary(self):
        """フレーム別集計のテスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp:
            csv_path = tmp.name
        
        try:
            self.create_test_coded_csv(csv_path)
            df = pd.read_csv(csv_path)
            
            summary = calculate_frame_summary(df)
            
            # Check structure
            assert len(summary) == 2  # Loss and Gain
            assert summary.loc['Loss', 'n_comments'] == 5
            assert summary.loc['Gain', 'n_comments'] == 5
            
            # Check VP rates (Loss: 3/5 = 0.6, Gain: 1/5 = 0.2)
            assert summary.loc['Loss', 'VP_rate'] == 0.6
            assert summary.loc['Gain', 'VP_rate'] == 0.2
            
            # Check E_ext rates (Loss: 1/5 = 0.2, Gain: 3/5 = 0.6)
            assert summary.loc['Loss', 'E_ext_rate'] == 0.2
            assert summary.loc['Gain', 'E_ext_rate'] == 0.6
            
            # Check medians
            assert summary.loc['Loss', 'median_like'] == 5  # [0, 2, 5, 10, 20] -> 5
            assert summary.loc['Gain', 'median_like'] == 8  # [1, 3, 8, 15, 25] -> 8
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    def test_calculate_video_summary(self):
        """動画別集計のテスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp:
            csv_path = tmp.name
        
        try:
            self.create_test_coded_csv(csv_path)
            df = pd.read_csv(csv_path)
            
            summary = calculate_video_summary(df)
            
            # Check structure
            assert len(summary) == 4  # v1, v2, v3, v4
            assert set(summary.columns) == {'frame', 'n_comments', 'VP_rate', 'E_ext_rate', 'E_int_rate', 'median_like', 'median_reply'}
            
            # Check specific values
            v1_summary = summary.loc['v1']
            assert v1_summary['n_comments'] == 3
            assert v1_summary['VP_rate'] == 2/3  # 2 out of 3
            assert v1_summary['frame'] == 'Loss'
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    def test_perform_hypothesis_tests(self):
        """仮説検定のテスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp:
            csv_path = tmp.name
        
        try:
            self.create_test_coded_csv(csv_path)
            df = pd.read_csv(csv_path)
            
            tests = perform_hypothesis_tests(df)
            
            # Check structure
            assert len(tests) >= 2  # At least H1 and H2
            
            # Check H1 test (VP rates)
            h1_test = tests[tests['hypothesis'] == 'H1'].iloc[0]
            assert 'p_value' in h1_test
            assert 0 <= h1_test['p_value'] <= 1
            assert h1_test['effect_size'] == pytest.approx(0.4, abs=0.01)  # 0.6 - 0.2
            
            # Check H2 test (E_ext rates)
            h2_test = tests[tests['hypothesis'] == 'H2'].iloc[0]
            assert 'p_value' in h1_test
            assert 0 <= h2_test['p_value'] <= 1
            assert h2_test['effect_size'] == pytest.approx(-0.4, abs=0.01)  # 0.2 - 0.6
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    def test_generate_report(self):
        """レポート生成の統合テスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp:
            csv_path = tmp.name
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = tmpdir
        
        try:
            self.create_test_coded_csv(csv_path)
            generator = ReportGenerator()
            
            generator.generate_report(csv_path, output_dir)
            
            # Check output files exist
            assert Path(output_dir, 'summary_by_frame.csv').exists()
            assert Path(output_dir, 'summary_by_video.csv').exists()
            assert Path(output_dir, 'tests_h1_h2.csv').exists()
            
            # Check content
            frame_summary = pd.read_csv(Path(output_dir, 'summary_by_frame.csv'))
            assert len(frame_summary) == 2
            assert 'VP_rate' in frame_summary.columns
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    def test_handle_missing_values(self):
        """欠損値の処理テスト"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w') as tmp:
            csv_path = tmp.name
        
        try:
            # Create CSV with missing values
            data = [
                {'video_id': 'v1', 'comment_id': 'c1', 'frame': 'Loss', 
                 'VP': '1', 'E_int': '', 'E_ext': '0', 'Cyn': '0', 'like_count': '10', 'total_reply_count': '0'},
                {'video_id': 'v1', 'comment_id': 'c2', 'frame': 'Loss', 
                 'VP': '', 'E_int': '0', 'E_ext': '1', 'Cyn': '0', 'like_count': '5', 'total_reply_count': '0'},
            ]
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['video_id', 'comment_id', 'frame', 'VP', 'E_int', 'E_ext', 'Cyn', 'like_count', 'total_reply_count']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            
            df = pd.read_csv(csv_path)
            summary = calculate_frame_summary(df)
            
            # Should handle missing values gracefully
            assert summary.loc['Loss', 'n_comments'] == 2
            # VP_rate should be 1/1 (one valid value)
            assert summary.loc['Loss', 'VP_rate'] == 1.0
            
        finally:
            Path(csv_path).unlink(missing_ok=True)