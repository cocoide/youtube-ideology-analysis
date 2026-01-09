#!/usr/bin/env python3
"""既存のコーディング済みCSVに動画公開日を追加"""

import pandas as pd

# Load existing data
df = pd.read_csv('out/coded_full_simulation.csv')

# Add video published dates (simulated)
video_dates = {
    'hj50Suuh5DM': '2024-01-01T00:00:00Z',
    'GLbc9in9zeY': '2024-01-01T00:00:00Z',
    'RF8I4LHej5E': '2024-01-15T00:00:00Z',
    'Ygtmbwj0sV4': '2024-01-15T00:00:00Z'
}

df['video_published_at'] = df['video_id'].map(video_dates)

# Save updated file
df.to_csv('out/coded_full_simulation_dated.csv', index=False)
print(f"Added video_published_at to {len(df)} comments")
print("Saved as: out/coded_full_simulation_dated.csv")