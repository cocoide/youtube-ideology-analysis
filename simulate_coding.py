#!/usr/bin/env python3
"""コーディングシートを仮ラベルで埋めてレポート生成のシミュレーション"""

import pandas as pd
import random
import csv
from pathlib import Path

# Load coding sheet
coding_sheet_path = 'out/coding_sheet_sample.csv'
if not Path(coding_sheet_path).exists():
    print(f"Error: {coding_sheet_path} not found")
    print("Run: python3 -m yt_pilot make-coding-sheet --db out/samples/all_samples_20260110_023820.sqlite --out out/coding_sheet_sample.csv")
    exit(1)

# Read coding sheet
df = pd.read_csv(coding_sheet_path)
print(f"Loaded {len(df)} comments from coding sheet")

# Add frame information based on video_id
# Since we only have hj50Suuh5DM in the sample, let's simulate with random assignment
# In real analysis, this would come from sample_videos.csv
df['frame'] = 'Loss'  # hj50Suuh5DM is a Loss frame video

# Simulate manual coding based on predictions + some noise
random.seed(42)

for idx, row in df.iterrows():
    # VP: Use prediction with 80% accuracy
    if random.random() < 0.8:
        df.at[idx, 'VP'] = str(row['pred_VP'])
    else:
        df.at[idx, 'VP'] = str(1 - int(row['pred_VP']))
    
    # E_ext: Use prediction with 70% accuracy + boost for certain keywords
    if '変える' in row['text'] or '声' in row['text']:
        df.at[idx, 'E_ext'] = '1'
    elif random.random() < 0.7:
        df.at[idx, 'E_ext'] = str(row['pred_E_ext'])
    else:
        df.at[idx, 'E_ext'] = str(1 - int(row['pred_E_ext']))
    
    # E_int: Similar approach
    if random.random() < 0.75:
        df.at[idx, 'E_int'] = str(row['pred_E_int'])
    else:
        df.at[idx, 'E_int'] = str(1 - int(row['pred_E_int']))
    
    # Cyn: Cynicism tends to be higher in Loss frame
    if 'どうせ' in row['text'] or '無駄' in row['text'] or '変わらない' in row['text']:
        df.at[idx, 'Cyn'] = '1'
    elif random.random() < 0.3:  # 30% chance of cynicism
        df.at[idx, 'Cyn'] = '1'
    else:
        df.at[idx, 'Cyn'] = '0'

# Save simulated coded data
output_path = 'out/coded_simulation.csv'
df.to_csv(output_path, index=False)
print(f"\nSaved simulated coded data to: {output_path}")

# Quick analysis
print("\n=== Quick Analysis of Coded Data ===")
print(f"Total comments: {len(df)}")
print(f"\nVP (Vote Pledge) rate: {df['VP'].astype(int).mean():.2%}")
print(f"E_ext (External Efficacy) rate: {df['E_ext'].astype(int).mean():.2%}")
print(f"E_int (Internal Efficacy) rate: {df['E_int'].astype(int).mean():.2%}")
print(f"Cyn (Cynicism) rate: {df['Cyn'].astype(int).mean():.2%}")

# Text analysis
print("\n=== Sample Comments by Category ===")

# High VP comments
vp_comments = df[df['VP'] == '1'].nlargest(3, 'like_count')
print("\n[投票宣言 (VP=1) の例]")
for _, comment in vp_comments.iterrows():
    print(f"- {comment['text'][:60]}... (likes: {comment['like_count']})")

# High Cynicism comments
cyn_comments = df[df['Cyn'] == '1'].nlargest(3, 'like_count')
print("\n[シニシズム (Cyn=1) の例]")
for _, comment in cyn_comments.iterrows():
    print(f"- {comment['text'][:60]}... (likes: {comment['like_count']})")

print("\n\nTo generate full report, run:")
print("python3 -m yt_pilot report --coded out/coded_simulation.csv --out out/reports --videos sample_videos.csv")