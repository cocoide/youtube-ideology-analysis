"""Advanced report generation with robustness checks"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from .report import perform_hypothesis_tests, calculate_frame_summary


def filter_by_days_since_video(df: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """Filter comments to within N days of video publication"""
    df = df.copy()
    
    # Convert dates
    df['video_published_at_dt'] = pd.to_datetime(df['video_published_at'])
    df['published_at_dt'] = pd.to_datetime(df['published_at'])
    
    # Calculate days since video
    df['days_since_video'] = (df['published_at_dt'] - df['video_published_at_dt']).dt.days
    
    # Filter
    filtered = df[df['days_since_video'] <= days].copy()
    
    # Drop helper columns
    filtered = filtered.drop(columns=['video_published_at_dt', 'published_at_dt', 'days_since_video'])
    
    return filtered


def perform_loo_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Perform Leave-One-Out analysis for robustness check"""
    results = []
    
    # Get unique videos
    videos = df['video_id'].unique()
    
    # Full analysis (no exclusion)
    full_tests = perform_hypothesis_tests(df)
    h1_full = full_tests[full_tests['hypothesis'] == 'H1'].iloc[0]
    h2_full = full_tests[full_tests['hypothesis'] == 'H2'].iloc[0]
    
    results.append({
        'excluded_video': 'none',
        'n_comments': len(df),
        'H1_p_value': h1_full['p_value'],
        'H1_effect_size': h1_full['effect_size'],
        'H2_p_value': h2_full['p_value'],
        'H2_effect_size': h2_full['effect_size']
    })
    
    # LOO for each video
    for video in videos:
        df_loo = df[df['video_id'] != video].copy()
        
        if len(df_loo) > 0:
            try:
                loo_tests = perform_hypothesis_tests(df_loo)
                h1_loo = loo_tests[loo_tests['hypothesis'] == 'H1'].iloc[0]
                h2_loo = loo_tests[loo_tests['hypothesis'] == 'H2'].iloc[0]
                
                results.append({
                    'excluded_video': video,
                    'n_comments': len(df_loo),
                    'H1_p_value': h1_loo['p_value'],
                    'H1_effect_size': h1_loo['effect_size'],
                    'H2_p_value': h2_loo['p_value'],
                    'H2_effect_size': h2_loo['effect_size']
                })
            except:
                # If test fails (e.g., not enough data), skip
                pass
    
    return pd.DataFrame(results)


def calculate_engagement_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate engagement-based metrics"""
    # Convert to numeric
    df = df.copy()
    df['like_count'] = pd.to_numeric(df['like_count'], errors='coerce').fillna(0)
    df['total_reply_count'] = pd.to_numeric(df['total_reply_count'], errors='coerce').fillna(0)
    
    # Add engagement flags
    df['has_like'] = (df['like_count'] > 0).astype(int)
    df['has_reply'] = (df['total_reply_count'] > 0).astype(int)
    df['high_engagement'] = ((df['like_count'] > 5) | (df['total_reply_count'] > 0)).astype(int)
    
    # Group by frame
    metrics = df.groupby('frame').agg({
        'has_like': 'mean',
        'has_reply': 'mean', 
        'high_engagement': 'mean',
        'like_count': ['mean', lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0]
    })
    
    # Flatten column names
    metrics.columns = ['has_like_rate', 'has_reply_rate', 'high_engagement_rate', 
                       'avg_like_all', 'avg_like_if_any']
    
    return metrics


class AdvancedReportGenerator:
    """Generate advanced analysis reports with robustness checks"""
    
    def load_data_with_frame(self, coded_csv: str, video_csv: Optional[str] = None) -> pd.DataFrame:
        """Load coded data and ensure frame information exists"""
        df = pd.read_csv(coded_csv)
        
        # If video metadata provided, use it
        if video_csv and Path(video_csv).exists():
            video_df = pd.read_csv(video_csv)
            if 'frame' in video_df.columns:
                df = df.merge(video_df[['video_id', 'frame']], on='video_id', how='left')
        
        # Fallback: infer from video_id if known
        if 'frame' not in df.columns:
            frame_mapping = {
                'hj50Suuh5DM': 'Loss',
                'GLbc9in9zeY': 'Loss',
                'RF8I4LHej5E': 'Loss',  # Actually Loss despite simulation
                'Ygtmbwj0sV4': 'Gain'
            }
            df['frame'] = df['video_id'].map(frame_mapping)
        
        return df
    
    def generate_advanced_report(self, coded_csv: str, output_dir: str, 
                                video_csv: Optional[str] = None,
                                days_filter: Optional[int] = 14,
                                include_loo: bool = True,
                                include_engagement: bool = True):
        """Generate comprehensive report with robustness checks"""
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Load data
        df = self.load_data_with_frame(coded_csv, video_csv)
        print(f"Loaded {len(df)} comments")
        
        # 1. Time-filtered analysis
        if days_filter:
            df_filtered = filter_by_days_since_video(df, days=days_filter)
            print(f"\nFiltered to {len(df_filtered)} comments within {days_filter} days")
            
            if len(df_filtered) > 0:
                summary_filtered = calculate_frame_summary(df_filtered)
                summary_filtered.to_csv(Path(output_dir) / f'summary_{days_filter}days.csv')
                
                tests_filtered = perform_hypothesis_tests(df_filtered)
                tests_filtered.to_csv(Path(output_dir) / f'tests_{days_filter}days.csv', index=False)
        
        # 2. LOO analysis
        if include_loo:
            print("\nPerforming Leave-One-Out analysis...")
            loo_results = perform_loo_analysis(df)
            loo_results.to_csv(Path(output_dir) / 'loo_analysis.csv', index=False)
            
            # Interpret robustness
            robustness_text = self._interpret_robustness(loo_results)
            with open(Path(output_dir) / 'robustness_report.txt', 'w') as f:
                f.write(robustness_text)
            print(robustness_text)
        
        # 3. Engagement metrics
        if include_engagement:
            print("\nCalculating engagement metrics...")
            engagement = calculate_engagement_metrics(df)
            engagement.to_csv(Path(output_dir) / 'engagement_metrics.csv')
            
            # VP by engagement level
            df_copy = df.copy()
            df_copy['VP'] = pd.to_numeric(df_copy['VP'], errors='coerce')
            df_copy['like_count'] = pd.to_numeric(df_copy['like_count'], errors='coerce')
            df_copy['has_engagement'] = (df_copy['like_count'] > 0).astype(int)
            
            vp_by_engagement = df_copy.groupby(['frame', 'has_engagement'])['VP'].mean()
            vp_by_engagement.to_csv(Path(output_dir) / 'vp_by_engagement.csv')
    
    def _interpret_robustness(self, loo_results: pd.DataFrame) -> str:
        """Interpret LOO results for robustness"""
        full_row = loo_results[loo_results['excluded_video'] == 'none'].iloc[0]
        loo_only = loo_results[loo_results['excluded_video'] != 'none']
        
        text = "=== Robustness Analysis Report ===\n\n"
        
        # H1 robustness
        h1_p_values = loo_only['H1_p_value'].values
        h1_significant = (h1_p_values < 0.05).sum()
        h1_total = len(h1_p_values)
        
        text += f"H1 (Loss → VP):\n"
        text += f"- Full analysis p-value: {full_row['H1_p_value']:.3f}\n"
        text += f"- Significant in {h1_significant}/{h1_total} LOO iterations\n"
        text += f"- P-value range: {h1_p_values.min():.3f} - {h1_p_values.max():.3f}\n"
        
        if h1_significant == h1_total:
            text += "- Assessment: ROBUST (always significant)\n"
        elif h1_significant >= h1_total * 0.75:
            text += "- Assessment: MOSTLY ROBUST\n"
        elif h1_significant >= h1_total * 0.5:
            text += "- Assessment: SENSITIVE (varies by video)\n"
        else:
            text += "- Assessment: NOT ROBUST\n"
        
        # H2 robustness
        text += f"\nH2 (Gain → E_ext):\n"
        h2_p_values = loo_only['H2_p_value'].values
        h2_significant = (h2_p_values < 0.05).sum()
        h2_total = len(h2_p_values)
        
        text += f"- Full analysis p-value: {full_row['H2_p_value']:.6f}\n"
        text += f"- Significant in {h2_significant}/{h2_total} LOO iterations\n"
        text += f"- P-value range: {h2_p_values.min():.6f} - {h2_p_values.max():.6f}\n"
        
        if h2_significant == h2_total:
            text += "- Assessment: ROBUST (always significant)\n"
        elif h2_significant >= h2_total * 0.75:
            text += "- Assessment: MOSTLY ROBUST\n"
        else:
            text += "- Assessment: SENSITIVE\n"
        
        # Effect size stability
        text += f"\n=== Effect Size Stability ===\n"
        text += f"H1 effect size range: {loo_only['H1_effect_size'].min():.3f} to {loo_only['H1_effect_size'].max():.3f}\n"
        text += f"H2 effect size range: {loo_only['H2_effect_size'].min():.3f} to {loo_only['H2_effect_size'].max():.3f}\n"
        
        return text


def generate_advanced_report_cli(coded_csv: str, output_dir: str, 
                                video_csv: Optional[str] = None,
                                days: Optional[int] = 14):
    """CLI function for advanced report"""
    generator = AdvancedReportGenerator()
    generator.generate_advanced_report(
        coded_csv, output_dir, video_csv,
        days_filter=days,
        include_loo=True,
        include_engagement=True
    )