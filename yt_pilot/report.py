"""Report generation for hypothesis testing"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
from scipy import stats


def calculate_frame_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate summary statistics by frame"""
    # Convert string columns to numeric
    numeric_cols = ['VP', 'E_int', 'E_ext', 'Cyn', 'Norm', 'Info', 'like_count', 'total_reply_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Group by frame
    summary = df.groupby('frame').agg({
        'comment_id': 'count',
        'VP': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'E_int': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'E_ext': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'Cyn': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'like_count': lambda x: x.dropna().median() if len(x.dropna()) > 0 else 0,
        'total_reply_count': lambda x: x.dropna().median() if len(x.dropna()) > 0 else 0,
    })
    
    # Rename columns
    summary.columns = [
        'n_comments', 'VP_rate', 'E_int_rate', 'E_ext_rate', 
        'Cyn_rate', 'median_like', 'median_reply'
    ]
    
    return summary


def calculate_video_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate summary statistics by video"""
    # Convert string columns to numeric
    numeric_cols = ['VP', 'E_int', 'E_ext', 'Cyn', 'Norm', 'Info', 'like_count', 'total_reply_count']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Group by video
    summary = df.groupby('video_id').agg({
        'frame': 'first',
        'comment_id': 'count',
        'VP': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'E_int': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'E_ext': lambda x: x.dropna().mean() if len(x.dropna()) > 0 else 0,
        'like_count': lambda x: x.dropna().median() if len(x.dropna()) > 0 else 0,
        'total_reply_count': lambda x: x.dropna().median() if len(x.dropna()) > 0 else 0,
    })
    
    # Rename columns
    summary.columns = [
        'frame', 'n_comments', 'VP_rate', 'E_int_rate', 'E_ext_rate', 
        'median_like', 'median_reply'
    ]
    
    return summary


def perform_hypothesis_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Perform hypothesis tests for H1 and H2"""
    results = []
    
    # Convert to numeric
    numeric_cols = ['VP', 'E_int', 'E_ext']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Split by frame
    loss_df = df[df['frame'] == 'Loss'].copy()
    gain_df = df[df['frame'] == 'Gain'].copy()
    
    # H1: VP rate difference (Loss > Gain expected)
    if 'VP' in df.columns:
        loss_vp = loss_df['VP'].dropna()
        gain_vp = gain_df['VP'].dropna()
        
        if len(loss_vp) > 0 and len(gain_vp) > 0:
            # Two-proportion z-test
            n1, n2 = len(loss_vp), len(gain_vp)
            x1, x2 = loss_vp.sum(), gain_vp.sum()
            
            # Pooled proportion
            p_pool = (x1 + x2) / (n1 + n2)
            se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
            
            # Z statistic
            p1, p2 = x1/n1, x2/n2
            z_stat = (p1 - p2) / se if se > 0 else 0
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            
            results.append({
                'hypothesis': 'H1',
                'method': 'Two-proportion z-test',
                'statistic': z_stat,
                'p_value': p_value,
                'effect_size': p1 - p2,
                'notes': f'Loss VP rate: {p1:.3f}, Gain VP rate: {p2:.3f}'
            })
    
    # H2: E_ext rate difference (Gain > Loss expected)
    if 'E_ext' in df.columns:
        loss_e_ext = loss_df['E_ext'].dropna()
        gain_e_ext = gain_df['E_ext'].dropna()
        
        if len(loss_e_ext) > 0 and len(gain_e_ext) > 0:
            # Two-proportion z-test
            n1, n2 = len(loss_e_ext), len(gain_e_ext)
            x1, x2 = loss_e_ext.sum(), gain_e_ext.sum()
            
            # Pooled proportion
            p_pool = (x1 + x2) / (n1 + n2)
            se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
            
            # Z statistic
            p1, p2 = x1/n1, x2/n2
            z_stat = (p1 - p2) / se if se > 0 else 0
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
            
            results.append({
                'hypothesis': 'H2',
                'method': 'Two-proportion z-test',
                'statistic': z_stat,
                'p_value': p_value,
                'effect_size': p1 - p2,
                'notes': f'Loss E_ext rate: {p1:.3f}, Gain E_ext rate: {p2:.3f}'
            })
    
    # Additional: Chi-square tests
    # H1 Chi-square
    if 'VP' in df.columns:
        contingency_table = pd.crosstab(df['frame'], df['VP'])
        if contingency_table.shape == (2, 2):
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            results.append({
                'hypothesis': 'H1',
                'method': 'Chi-square test',
                'statistic': chi2,
                'p_value': p_value,
                'effect_size': np.sqrt(chi2 / df.shape[0]),  # Cramér's V
                'notes': f'Degrees of freedom: {dof}'
            })
    
    return pd.DataFrame(results)


class ReportGenerator:
    """Generate analysis reports from coded data"""
    
    def __init__(self):
        pass
    
    def load_coded_data(self, coded_csv: str, video_csv: Optional[str] = None) -> pd.DataFrame:
        """Load coded data and optionally merge with video metadata"""
        df = pd.read_csv(coded_csv)
        
        # If video metadata is provided, merge it
        if video_csv:
            video_df = pd.read_csv(video_csv)
            if 'frame' in video_df.columns:
                df = df.merge(video_df[['video_id', 'frame']], on='video_id', how='left')
        
        # If frame column doesn't exist, try to infer from video_id
        if 'frame' not in df.columns:
            # This is a fallback - in real usage, frame should come from metadata
            print("Warning: No frame information found. Results may be incomplete.")
        
        return df
    
    def generate_report(self, coded_csv: str, output_dir: str, video_csv: Optional[str] = None):
        """Generate all report files"""
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load data
        df = self.load_coded_data(coded_csv, video_csv)
        
        # Generate summaries
        if 'frame' in df.columns:
            frame_summary = calculate_frame_summary(df)
            frame_summary.to_csv(Path(output_dir) / 'summary_by_frame.csv')
            print(f"Generated: {Path(output_dir) / 'summary_by_frame.csv'}")
        
        video_summary = calculate_video_summary(df)
        video_summary.to_csv(Path(output_dir) / 'summary_by_video.csv')
        print(f"Generated: {Path(output_dir) / 'summary_by_video.csv'}")
        
        # Perform tests
        if 'frame' in df.columns:
            test_results = perform_hypothesis_tests(df)
            test_results.to_csv(Path(output_dir) / 'tests_h1_h2.csv', index=False)
            print(f"Generated: {Path(output_dir) / 'tests_h1_h2.csv'}")
            
            # Print summary
            print("\n=== Hypothesis Test Results ===")
            for _, test in test_results.iterrows():
                print(f"\n{test['hypothesis']} ({test['method']}):")
                print(f"  Statistic: {test['statistic']:.3f}")
                print(f"  p-value: {test['p_value']:.3f}")
                print(f"  Effect size: {test['effect_size']:.3f}")
                print(f"  Notes: {test['notes']}")


def generate_report_cli(coded_csv: str, output_dir: str, video_csv: Optional[str] = None):
    """CLI function to generate report"""
    generator = ReportGenerator()
    generator.generate_report(coded_csv, output_dir, video_csv)