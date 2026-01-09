#!/usr/bin/env python3
"""複数動画でのフレーム効果シミュレーション"""

import pandas as pd
import numpy as np
import random

# Set random seed
random.seed(42)
np.random.seed(42)

# Create simulated data for 4 videos (2 Loss, 2 Gain)
data = []

# Loss frame videos
loss_videos = ['hj50Suuh5DM', 'GLbc9in9zeY']
gain_videos = ['Ygtmbwj0sV4', 'RF8I4LHej5E']  # Note: RF8I4LHej5E is actually Loss, but simulating as Gain for demo

video_frames = {
    'hj50Suuh5DM': 'Loss',
    'GLbc9in9zeY': 'Loss', 
    'Ygtmbwj0sV4': 'Gain',
    'RF8I4LHej5E': 'Gain'
}

# Generate synthetic comments
comment_id = 1
for video_id, frame in video_frames.items():
    n_comments = random.randint(80, 120)
    
    for i in range(n_comments):
        # Base probabilities depend on frame
        if frame == 'Loss':
            vp_prob = 0.35  # Higher VP in Loss frame (H1)
            e_ext_prob = 0.15  # Lower E_ext in Loss frame (H2)
            cyn_prob = 0.40  # Higher cynicism in Loss frame
        else:  # Gain
            vp_prob = 0.20  # Lower VP in Gain frame
            e_ext_prob = 0.35  # Higher E_ext in Gain frame (H2)
            cyn_prob = 0.20  # Lower cynicism in Gain frame
        
        comment = {
            'video_id': video_id,
            'comment_id': f'c{comment_id}',
            'frame': frame,
            'published_at': f'2024-01-{random.randint(1, 30):02d}T{random.randint(0, 23):02d}:00:00Z',
            'like_count': np.random.poisson(3),  # Poisson distribution for likes
            'total_reply_count': np.random.poisson(0.5),  # Most comments have no replies
            'text': f'Sample comment {comment_id}',
            'VP': '1' if random.random() < vp_prob else '0',
            'E_ext': '1' if random.random() < e_ext_prob else '0',
            'E_int': '1' if random.random() < 0.25 else '0',  # Constant across frames
            'Cyn': '1' if random.random() < cyn_prob else '0',
            'Norm': '1' if random.random() < 0.15 else '0',
            'Info': '1' if random.random() < 0.10 else '0',
            'unsure': '',
            'coder_memo': ''
        }
        
        data.append(comment)
        comment_id += 1

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV
output_path = 'out/coded_full_simulation.csv'
df.to_csv(output_path, index=False)
print(f"Generated {len(df)} simulated comments")
print(f"Saved to: {output_path}")

# Quick preview
print("\n=== Data Summary ===")
summary = df.groupby('frame').agg({
    'comment_id': 'count',
    'VP': lambda x: pd.to_numeric(x).mean(),
    'E_ext': lambda x: pd.to_numeric(x).mean(),
    'Cyn': lambda x: pd.to_numeric(x).mean(),
    'like_count': 'mean'
})
summary.columns = ['n_comments', 'VP_rate', 'E_ext_rate', 'Cyn_rate', 'avg_likes']
print(summary)

print("\n\nNow run:")
print("python3 -m yt_pilot report --coded out/coded_full_simulation.csv --out out/reports")